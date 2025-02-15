# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2021 Recidiviz, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# =============================================================================
"""Defines routes for the Justice Counts API endpoints in the admin panel."""

import itertools
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple

import attr
import pandas as pd
from flask import Blueprint, Response, jsonify, request
from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy.exc import IntegrityError

from recidiviz.auth.auth0_client import Auth0Client, Auth0User
from recidiviz.justice_counts.agency import AgencyInterface
from recidiviz.justice_counts.bulk_upload.bulk_upload import BulkUploader
from recidiviz.justice_counts.user_account import UserAccountInterface
from recidiviz.persistence.database.schema.justice_counts import schema
from recidiviz.persistence.database.schema_utils import SchemaType
from recidiviz.persistence.database.session import Session
from recidiviz.persistence.database.session_factory import SessionFactory
from recidiviz.persistence.database.sqlalchemy_database_key import SQLAlchemyDatabaseKey
from recidiviz.utils.auth.gae import requires_gae_auth
from recidiviz.utils.types import assert_type, non_optional


@attr.define()
class JusticeCountsUser:
    auth0_user_id: str
    auth0_email: str
    auth0_name: str
    db_name: Optional[str] = None
    db_id: Optional[int] = None
    agency_ids: List[int] = attr.field(factory=list)
    agencies: List[Dict[str, Any]] = attr.field(factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            "auth0_user_id": self.auth0_user_id,
            "auth0_email": self.auth0_email,
            "auth0_name": self.auth0_name,
            "db_name": self.db_name,
            "db_id": self.db_id,
            "agencies": self.agencies,
        }


_auth0_client = None


def _get_auth0_client() -> Auth0Client:
    """Returns a Justice Counts Auth0 client, lazily generating one if we have not
    already.
    """
    global _auth0_client
    if not _auth0_client:
        _auth0_client = Auth0Client(  # nosec
            domain_secret_name="justice_counts_auth0_api_domain",
            client_id_secret_name="justice_counts_auth0_api_client_id",
            client_secret_secret_name="justice_counts_auth0_api_client_secret",
        )
    return _auth0_client


def add_justice_counts_tools_routes(bp: Blueprint) -> None:
    """Adds the relevant Justice Counts Admin Panel API routes to an input Blueprint."""

    @bp.route("/api/justice_counts_tools/agencies", methods=["GET"])
    @requires_gae_auth
    def get_all_agencies() -> Tuple[Response, HTTPStatus]:
        """Returns all Agency records."""
        with SessionFactory.using_database(
            SQLAlchemyDatabaseKey.for_schema(SchemaType.JUSTICE_COUNTS)
        ) as session:
            return (
                jsonify(
                    {
                        "agencies": [
                            agency.to_json()
                            for agency in AgencyInterface.get_agencies(session=session)
                        ],
                        "systems": [enum.value for enum in schema.System],
                    }
                ),
                HTTPStatus.OK,
            )

    @bp.route("/api/justice_counts_tools/agencies", methods=["POST"])
    @requires_gae_auth
    def create_agency() -> Tuple[Response, HTTPStatus]:
        """Creates an Agency and returns the created Agency.
        Returns an error message if the Agency already exists with that name.
        """
        try:
            with SessionFactory.using_database(
                SQLAlchemyDatabaseKey.for_schema(SchemaType.JUSTICE_COUNTS)
            ) as session:
                request_json = assert_type(request.json, dict)
                name = assert_type(request_json.get("name"), str)
                systems: List[str] = non_optional(request_json.get("systems"))
                user_account_id: int = assert_type(
                    request_json.get("user_account_id"), int
                )
                state_code = assert_type(request_json.get("state_code"), str)
                fips_county_code = request_json.get("fips_county_code")
                agency = AgencyInterface.create_agency(
                    session=session,
                    name=name,
                    systems=[schema.System[system] for system in systems],
                    state_code=state_code,
                    user_account_id=user_account_id,
                    fips_county_code=fips_county_code,
                )
                return (
                    jsonify({"agency": agency.to_json()}),
                    HTTPStatus.OK,
                )
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolation):  # proves the original exception
                return (
                    jsonify({"error": "Agency already exists."}),
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            raise e

    @bp.route("/api/justice_counts_tools/users", methods=["GET"])
    @requires_gae_auth
    def get_all_users() -> Tuple[Response, HTTPStatus]:
        """Returns all UserAccount records. Joins the records in our database with the
        records obtained by the Auth0 management API.
        """
        auth0_users = _get_auth0_client().get_all_users()

        with SessionFactory.using_database(
            SQLAlchemyDatabaseKey.for_schema(SchemaType.JUSTICE_COUNTS)
        ) as session:
            db_users = UserAccountInterface.get_users(session=session)
            all_users = _merge_auth0_and_db_users(
                session=session, auth0_users=auth0_users, db_users=db_users
            )

        return (
            jsonify({"users": [user.to_json() for user in all_users]}),
            HTTPStatus.OK,
        )

    @bp.route("/api/justice_counts_tools/users", methods=["PUT"])
    @requires_gae_auth
    def update_user() -> Tuple[Response, HTTPStatus]:
        """
        Updates a User. If name is provided, update in our DB and Auth0.
        If agencies are provided, update in Auth0.
        """
        with SessionFactory.using_database(
            SQLAlchemyDatabaseKey.for_schema(SchemaType.JUSTICE_COUNTS)
        ) as session:
            request_json = assert_type(request.json, dict)
            name = request_json.get("name")
            auth0_user_id = request_json.get("auth0_user_id")
            agency_ids = request_json.get("agency_ids")

            if auth0_user_id is None:
                raise ValueError("auth0_user_id is required")

            if name is not None:
                UserAccountInterface.create_or_update_user(
                    session=session,
                    name=name,
                    auth0_user_id=auth0_user_id,
                )

            if name is not None or agency_ids is not None:
                app_metadata = (
                    {"agency_ids": agency_ids} if agency_ids is not None else None
                )
                _get_auth0_client().update_user(
                    user_id=auth0_user_id,
                    name=name,
                    app_metadata=app_metadata,
                )

            return (
                jsonify({"status": "ok"}),
                HTTPStatus.OK,
            )

    @bp.route("/api/justice_counts_tools/bulk_upload", methods=["POST"])
    @requires_gae_auth
    def bulk_upload() -> Tuple[str, HTTPStatus]:
        """Upload data for an agency."""
        file = request.files["file"]
        xls = pd.ExcelFile(file)

        data = assert_type(request.form, dict)
        agency_id = int(data["agency_id"])
        user_id = int(data["user_id"])
        system = data["system"]

        uploader = BulkUploader(catch_errors=False)

        with SessionFactory.using_database(
            SQLAlchemyDatabaseKey.for_schema(SchemaType.JUSTICE_COUNTS)
        ) as session:
            uploader.upload_excel(
                session=session,
                xls=xls,
                agency_id=agency_id,
                system=schema.System[system],
                user_account=session.query(schema.UserAccount).get(user_id),
            )
        return "", HTTPStatus.OK


def _merge_auth0_and_db_users(
    session: Session, auth0_users: List[Auth0User], db_users: List[schema.UserAccount]
) -> List[JusticeCountsUser]:
    """Given a list of users who have signed up via Auth0, and a list of
    users whom we have registered in our DB, perform a union and merge based on
    auth0 user id. Users who have the same auth0 user id will be considered
    the same user, and their Auth0 + DB metadata will be merged into one
    object. Users who only appear in one place will have their own object.
    """
    agency_ids_to_fetch = set()
    auth0_users_by_id = {user["user_id"]: user for user in auth0_users}
    all_users_by_auth0_id = {}

    for db_user in db_users:
        auth0_user_id = db_user.auth0_user_id
        matching_auth0_user = auth0_users_by_id.get(auth0_user_id)
        if not matching_auth0_user:
            # User just appears in our DB
            # This should actually never happen anymore!
            # (except when using fixture data)
            continue

        # User appears in both Auth0 and our DB
        all_users_by_auth0_id[auth0_user_id] = JusticeCountsUser(
            auth0_user_id=matching_auth0_user["user_id"],
            auth0_name=matching_auth0_user["name"],
            auth0_email=matching_auth0_user["email"],
            db_name=db_user.name,
            db_id=db_user.id,
            agency_ids=matching_auth0_user.get("app_metadata", {}).get("agency_ids", []),  # type: ignore[arg-type]
        )

    for auth0_user_id, auth0_user in auth0_users_by_id.items():
        if auth0_user_id not in all_users_by_auth0_id:
            # User just appears in Auth0
            all_users_by_auth0_id[auth0_user_id] = JusticeCountsUser(
                auth0_user_id=auth0_user["user_id"],
                auth0_name=auth0_user["name"],
                auth0_email=auth0_user["email"],
                agency_ids=auth0_user.get("app_metadata", {}).get("agency_ids", []),  # type: ignore[arg-type]
            )

    # Now fetch the Agencies that were referenced in any users metadata
    agency_ids_to_fetch = set(
        itertools.chain(*[user.agency_ids for user in all_users_by_auth0_id.values()])
    )
    agencies_by_id = {
        agency.id: agency
        for agency in AgencyInterface.get_agencies_by_id(
            session=session, agency_ids=list(agency_ids_to_fetch)
        )
    }
    for _, user in all_users_by_auth0_id.items():
        user.agencies = [
            agencies_by_id[agency_id].to_json()
            for agency_id in user.agency_ids
            if agency_id in agencies_by_id
        ]

    return list(all_users_by_auth0_id.values())
