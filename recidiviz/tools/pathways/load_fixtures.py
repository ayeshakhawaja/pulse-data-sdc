# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2022 Recidiviz, Inc.
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
"""
Tool for loading fixture data into our Pathways development database.

This script should be run only after `docker-compose up` has been run.
This will delete everything from the tables and then re-add them from the
fixture files.

Usage against default development database (docker-compose v1):
docker exec pulse-data_case_triage_backend_1 pipenv run python -m recidiviz.tools.pathways.load_fixtures

Usage against default development database (docker-compose v2):
docker exec pulse-data-case_triage_backend-1 pipenv run python -m recidiviz.tools.pathways.load_fixtures
"""
import logging
import os

from sqlalchemy.engine import Engine

from recidiviz.calculator.query.state.views.dashboard.pathways.pathways_enabled_states import (
    get_pathways_enabled_states,
)
from recidiviz.case_triage.pathways.pathways_database_manager import (
    PathwaysDatabaseManager,
)
from recidiviz.persistence.database.schema.pathways.schema import PathwaysBase
from recidiviz.persistence.database.schema_utils import get_pathways_table_classes
from recidiviz.persistence.database.sqlalchemy_engine_manager import (
    SQLAlchemyEngineManager,
)
from recidiviz.tools.utils.fixture_helpers import reset_fixtures
from recidiviz.utils.environment import in_development


def reset_pathways_fixtures(engine: Engine) -> None:
    """Deletes all ETL data and re-imports data from our fixture files"""
    reset_fixtures(
        engine=engine,
        tables=list(get_pathways_table_classes()),
        fixture_directory=os.path.join(
            os.path.dirname(__file__),
            "../../..",
            "recidiviz/tests/case_triage/pathways/fixtures",
        ),
        csv_headers=True,
    )


if __name__ == "__main__":
    if not in_development():
        raise RuntimeError(
            "Expected to be called inside a docker container. See usage in docstring"
        )

    logging.basicConfig(level=logging.INFO)

    for state in get_pathways_enabled_states():
        database_key = PathwaysDatabaseManager.database_key_for_state(state)
        pathways_engine = SQLAlchemyEngineManager.init_engine(database_key)

        PathwaysBase.metadata.create_all(pathways_engine)

        reset_pathways_fixtures(pathways_engine)