# Recidiviz - a data platform for criminal justice reform
# Copyright (C) 2019 Recidiviz, Inc.
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
"""Tests for the GCS Pseudo Lock Manager class"""
import json
import unittest
from datetime import datetime, timedelta
from unittest import mock

from recidiviz.cloud_storage.gcs_pseudo_lock_manager import (
    EXPIRATION_IN_SECONDS_KEY,
    LOCK_TIME_KEY,
    MAX_UNLOCK_ATTEMPTS,
    PAYLOAD_KEY,
    GCSPseudoLockAlreadyExists,
    GCSPseudoLockBody,
    GCSPseudoLockDoesNotExist,
    GCSPseudoLockFailedUnlock,
    GCSPseudoLockManager,
)
from recidiviz.cloud_storage.gcsfs_path import GcsfsFilePath
from recidiviz.tests.cloud_storage.fake_gcs_file_system import FakeGCSFileSystem


class TestGCSPseudoLockContents(unittest.TestCase):
    """Class to test GCSPseudoLockContents"""

    def test_to_json_no_optionals(self) -> None:
        now = datetime.now()
        body = GCSPseudoLockBody(lock_time=now)
        encoded_contents = body.to_json()

        self.assertEqual(encoded_contents[LOCK_TIME_KEY], now)
        self.assertTrue(PAYLOAD_KEY not in encoded_contents)
        self.assertTrue(EXPIRATION_IN_SECONDS_KEY not in encoded_contents)

    def test_to_json(self) -> None:
        now = datetime.now()
        text_payload = "SECRET_CONTENTS"
        expiration_in_seconds = 4
        body = GCSPseudoLockBody(
            lock_time=now,
            payload=text_payload,
            expiration_in_seconds=expiration_in_seconds,
        )
        encoded_contents = body.to_json()

        self.assertEqual(encoded_contents[LOCK_TIME_KEY], now)
        self.assertEqual(encoded_contents[PAYLOAD_KEY], text_payload)
        self.assertEqual(
            encoded_contents[EXPIRATION_IN_SECONDS_KEY], expiration_in_seconds
        )

    def test_from_json_failures(self) -> None:
        self.assertIsNone(GCSPseudoLockBody.from_json_string("malformed}{"))
        self.assertIsNone(GCSPseudoLockBody.from_json_string('"a string"'))
        self.assertIsNone(GCSPseudoLockBody.from_json_string('["a list"]'))
        self.assertIsNone(GCSPseudoLockBody.from_json_string("{}"))
        self.assertIsNone(GCSPseudoLockBody.from_json_string('{"lock_time": -4}'))
        self.assertIsNone(
            GCSPseudoLockBody.from_json_string(
                '{"lock_time": "2021-03-05 15:09:32.332362", "contents": 4}'
            )
        )
        self.assertIsNone(
            GCSPseudoLockBody.from_json_string(
                '{"lock_time": "2021-03-05 15:09:32.332362", "expiration_in_seconds": "4"}'
            )
        )

    def test_from_json_success(self) -> None:
        self.assertIsNotNone(
            GCSPseudoLockBody.from_json_string(
                '{"lock_time": "2021-03-05 15:09:32.332362"}'
            )
        )
        self.assertIsNotNone(
            GCSPseudoLockBody.from_json_string(
                '{"lock_time": "2021-03-05 15:09:32.332362", "contents": "4"}'
            )
        )
        self.assertIsNotNone(
            GCSPseudoLockBody.from_json_string(
                '{"lock_time": "2021-03-05 15:09:32.332362", "contents": "4", "expiration_in_seconds": 4}'
            )
        )
        self.assertIsNotNone(
            GCSPseudoLockBody.from_json_string(
                '{"lock_time": "2021-03-05 15:09:32.332362", "expiration_in_seconds": 4}'
            )
        )


class _FailingDeleteFs(FakeGCSFileSystem):
    """Fake FS implementation where delete always fails."""

    def delete(self, path: GcsfsFilePath) -> None:
        # Do nothing
        pass


class _MultipleAttemptDeleteFs(FakeGCSFileSystem):
    """Fake FS implementation where delete only succeeds after some retries."""

    def __init__(self) -> None:
        super().__init__()
        self.delete_attempts = 0

    def delete(self, path: GcsfsFilePath) -> None:
        if self.delete_attempts < MAX_UNLOCK_ATTEMPTS - 1:
            self.delete_attempts += 1
            return
        super().delete(path)


class TestGCSPseudoLockManager(unittest.TestCase):
    """Class to test GCS Pseudo Lock Manager"""

    LOCK_NAME = "LOCK_NAME"
    LOCK_NAME2 = "LOCK_NAME2"
    PROJECT_ID = "recidiviz-staging"
    TIME_FORMAT = "%m/%d/%Y, %H:%M:%S"
    CONTENTS = '{"CONTENTS" : "contents"}'
    CONTENTS2 = '{"CONTENTS2" : "contents2"}'
    REGION = "region"
    PREFIX = "prefix"

    def setUp(self) -> None:
        self.project_id_patcher = mock.patch(
            "recidiviz.cloud_storage.gcs_pseudo_lock_manager.metadata"
        )
        self.project_id_patcher.start().return_value = "recidiviz-123"
        self.gcs_factory_patcher = mock.patch(
            "recidiviz.cloud_storage.gcs_pseudo_lock_manager.GcsfsFactory.build"
        )
        fake_gcs = FakeGCSFileSystem()
        self.gcs_factory_patcher.start().return_value = fake_gcs
        self.fs = fake_gcs

    def tearDown(self) -> None:
        self.gcs_factory_patcher.stop()
        self.project_id_patcher.stop()

    def _upload_fake_expired_lock(
        self, lock_manager: GCSPseudoLockManager, lock_name: str
    ) -> None:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        path = GcsfsFilePath(bucket_name=lock_manager.bucket_name, blob_name=lock_name)
        self.fs.upload_from_string(
            path,
            json.dumps(
                GCSPseudoLockBody(
                    lock_time=yesterday, expiration_in_seconds=3600
                ).to_json(),
                default=str,
            ),
            content_type="text/text",
        )

    def test_lock(self) -> None:
        """Locks temp and then checks if locked"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME, expiration_in_seconds=3600)
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))

    def test_lock_unlock(self) -> None:
        """Locks then unlocks temp, checks if still locked"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        lock_manager.unlock(self.LOCK_NAME)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_lock_unlock_with_retry(self) -> None:
        """Locks then unlocks temp, checks if still locked"""

        self.gcs_factory_patcher.stop()
        self.gcs_factory_patcher.start().return_value = _MultipleAttemptDeleteFs()

        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        lock_manager.unlock(self.LOCK_NAME)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_double_lock_diff_contents(self) -> None:
        """Locks and then locks again with unique contents, asserts its still locked and an error is raised"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME, payload=self.CONTENTS)

        with self.assertRaises(GCSPseudoLockAlreadyExists):
            lock_manager.lock(self.LOCK_NAME, self.CONTENTS2)
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))
        self.assertEqual(self.CONTENTS, lock_manager.get_lock_payload(self.LOCK_NAME))

    def test_double_lock(self) -> None:
        """Locks and then locks again, asserts its still locked and an error is raised"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        with self.assertRaises(GCSPseudoLockAlreadyExists):
            lock_manager.lock(self.LOCK_NAME)
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))

    def test_double_unlock(self) -> None:
        """Unlocks and then unlocks gain, asserts its still unlocked and raises an error"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))
        with self.assertRaises(GCSPseudoLockDoesNotExist):
            lock_manager.unlock(self.LOCK_NAME)
        with self.assertRaises(GCSPseudoLockDoesNotExist):
            lock_manager.unlock(self.LOCK_NAME)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_lock_two_diff(self) -> None:
        """Locks two different locks, asserts both locked"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        lock_manager.lock(self.LOCK_NAME2)
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME2))

    def test_lock_unlock_two_diff(self) -> None:
        """Locks two different locks, unlocks both, asserts both unlocked"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        lock_manager.lock(self.LOCK_NAME2)
        lock_manager.unlock(self.LOCK_NAME)
        lock_manager.unlock(self.LOCK_NAME2)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME2))

    def test_lock_two_diff_unlock_one(self) -> None:
        """Locks two different locks, unlocks one, asserts both in correct place"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        lock_manager.lock(self.LOCK_NAME2)
        lock_manager.unlock(self.LOCK_NAME)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME2))

    def test_lock_one_unlock_other(self) -> None:
        """Locks one lock and unlocks another, asserts both have correct status"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        with self.assertRaises(GCSPseudoLockDoesNotExist):
            lock_manager.unlock(self.LOCK_NAME2)
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME2))

    def test_unlock_never_locked(self) -> None:
        """Unlocks a lock that has never been locked before, check it raises an error and remains locked"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        with self.assertRaises(GCSPseudoLockDoesNotExist):
            lock_manager.unlock(self.LOCK_NAME2)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_unlock_delete_fails(self) -> None:
        self.gcs_factory_patcher.stop()
        self.gcs_factory_patcher.start().return_value = _FailingDeleteFs()

        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)

        with self.assertRaises(GCSPseudoLockFailedUnlock):
            lock_manager.unlock(self.LOCK_NAME)

    def test_unlock_delete_fails_using_lock(self) -> None:
        self.gcs_factory_patcher.stop()
        self.gcs_factory_patcher.start().return_value = _FailingDeleteFs()

        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)

        with self.assertRaises(GCSPseudoLockFailedUnlock):
            with lock_manager.using_lock(self.LOCK_NAME):
                pass

    def test_contents_of_lock_default(self) -> None:
        """Locks with default contents and asserts the lockfile contains correct time"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME)
        path = GcsfsFilePath(
            bucket_name=lock_manager.bucket_name, blob_name=self.LOCK_NAME
        )
        actual_body = GCSPseudoLockBody.from_json_string(
            self.fs.download_as_string(path)
        )
        self.assertIsNotNone(actual_body)

    def test_contents_of_lock_set(self) -> None:
        """Locks with pre-specified contents and asserts the lockfile contains those contents"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME, self.CONTENTS)
        path = GcsfsFilePath(
            bucket_name=lock_manager.bucket_name, blob_name=self.LOCK_NAME
        )
        actual_body = GCSPseudoLockBody.from_json_string(
            self.fs.download_as_string(path)
        )

        assert actual_body is not None
        self.assertEqual(self.CONTENTS, actual_body.payload)

    def test_contents_of_unlocked_and_relocked(self) -> None:
        """Locks with pre-specified contents and asserts the lockfile contains those contents"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME, self.CONTENTS)
        lock_manager.unlock(self.LOCK_NAME)
        lock_manager.lock(self.LOCK_NAME, self.CONTENTS2)
        path = GcsfsFilePath(
            bucket_name=lock_manager.bucket_name, blob_name=self.LOCK_NAME
        )
        actual_body = GCSPseudoLockBody.from_json_string(
            self.fs.download_as_string(path)
        )

        assert actual_body is not None
        self.assertEqual(self.CONTENTS2, actual_body.payload)

    def test_locks_with_prefix_exist(self) -> None:
        """Ensures lock manager can see if locks with a prefix exist."""
        prefix = "SOME_LOCK_PREFIX"
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(prefix + "some_suffix")
        self.assertFalse(lock_manager.no_active_locks_with_prefix(prefix))

    def test_locks_with_prefix_do_not_exist(self) -> None:
        """Ensures lock manager can see regions are not running"""
        prefix = "SOME_LOCK_PREFIX"
        lock_name = prefix + "some_suffix"
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(lock_name)
        lock_manager.unlock(lock_name)
        self.assertTrue(lock_manager.no_active_locks_with_prefix(prefix))

    def test_locks_with_prefix_ignore_expired(self) -> None:
        """Ensures lock manager can see if locks with a prefix exist."""
        prefix = "SOME_LOCK_PREFIX"
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)

        self._upload_fake_expired_lock(lock_manager, prefix + "some_suffix")

        self.assertTrue(lock_manager.no_active_locks_with_prefix(prefix))

    def test_locks_with_prefix_mixed(self) -> None:
        """Ensures lock manager can see if locks with a prefix exist."""
        prefix = "SOME_LOCK_PREFIX"
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)

        self._upload_fake_expired_lock(lock_manager, prefix + "some_suffix")
        lock_manager.lock(prefix + "some_suffix2")

        self.assertFalse(lock_manager.no_active_locks_with_prefix(prefix))

    def test_get_lock_contents(self) -> None:
        """Tests that the get_lock_contents gets the correct contents from the lock"""
        lock_manager = GCSPseudoLockManager(self.PROJECT_ID)
        lock_manager.lock(self.LOCK_NAME, self.CONTENTS)
        actual_body = lock_manager.get_lock_payload(self.LOCK_NAME)
        self.assertEqual(self.CONTENTS, actual_body)

    def test_using_lock(self) -> None:
        lock_manager = GCSPseudoLockManager()
        with lock_manager.using_lock(self.LOCK_NAME, self.CONTENTS):
            self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))

            # Contents appropriately set
            actual_body = lock_manager.get_lock_payload(self.LOCK_NAME)
            self.assertEqual(self.CONTENTS, actual_body)

        # lock should be unlocked outside of with
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_raise_from_using_lock(self) -> None:
        lock_manager = GCSPseudoLockManager()

        with self.assertRaises(ValueError):
            with lock_manager.using_lock(self.LOCK_NAME, self.CONTENTS):
                raise ValueError

        # lock should be unlocked outside of with
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_using_lock_when_already_locked(self) -> None:
        lock_manager = GCSPseudoLockManager()
        lock_manager.lock(self.LOCK_NAME)

        with self.assertRaises(GCSPseudoLockAlreadyExists):
            with lock_manager.using_lock(self.LOCK_NAME, self.CONTENTS):
                pass

    def test_lock_expiration_not_met(self) -> None:
        now = datetime.now()
        lock_manager = GCSPseudoLockManager()

        path = GcsfsFilePath(
            bucket_name=lock_manager.bucket_name, blob_name=self.LOCK_NAME
        )
        self.fs.upload_from_string(
            path,
            json.dumps(
                GCSPseudoLockBody(lock_time=now, expiration_in_seconds=60).to_json(),
                default=str,
            ),
            content_type="text/text",
        )
        self.assertTrue(lock_manager.is_locked(self.LOCK_NAME))

    def test_lock_expired(self) -> None:
        lock_manager = GCSPseudoLockManager()
        self._upload_fake_expired_lock(lock_manager, self.LOCK_NAME)
        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

    def test_unlock_expired(self) -> None:
        lock_manager = GCSPseudoLockManager()

        self._upload_fake_expired_lock(lock_manager, self.LOCK_NAME)

        self.assertFalse(lock_manager.is_locked(self.LOCK_NAME))

        # Should not raise an error
        lock_manager.unlock(self.LOCK_NAME)
