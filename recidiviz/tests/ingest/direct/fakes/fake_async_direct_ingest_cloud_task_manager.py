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
"""Test implementation of the DirectIngestCloudTaskManager that runs tasks
asynchronously on background threads."""
from typing import Any, Callable

from recidiviz.cloud_storage.gcsfs_path import GcsfsBucketPath
from recidiviz.ingest.direct.controllers.gcsfs_direct_ingest_utils import (
    GcsfsIngestViewExportArgs,
    GcsfsRawDataBQImportArgs,
    LegacyExtractAndMergeArgs,
)
from recidiviz.ingest.direct.direct_ingest_cloud_task_manager import (
    IngestViewExportCloudTaskQueueInfo,
    ProcessIngestJobCloudTaskQueueInfo,
    RawDataImportCloudTaskQueueInfo,
    SchedulerCloudTaskQueueInfo,
    SftpCloudTaskQueueInfo,
    build_handle_new_files_task_id,
    build_ingest_view_export_task_id,
    build_process_job_task_id,
    build_raw_data_import_task_id,
    build_scheduler_task_id,
    build_sftp_download_task_id,
)
from recidiviz.ingest.direct.types.direct_ingest_instance import DirectIngestInstance
from recidiviz.ingest.direct.types.direct_ingest_instance_factory import (
    DirectIngestInstanceFactory,
)
from recidiviz.tests.ingest.direct.fakes.fake_direct_ingest_cloud_task_manager import (
    FakeDirectIngestCloudTaskManager,
)
from recidiviz.utils import monitoring
from recidiviz.utils.regions import Region
from recidiviz.utils.single_thread_task_queue import SingleThreadTaskQueue


def with_monitoring(
    region_code: str, ingest_instance: DirectIngestInstance, fn: Callable
) -> Callable:
    def wrapped_fn(*args: Any, **kwargs: Any) -> None:
        with monitoring.push_region_tag(region_code, ingest_instance.value):
            fn(*args, **kwargs)

    return wrapped_fn


class FakeAsyncDirectIngestCloudTaskManager(FakeDirectIngestCloudTaskManager):
    """Test implementation of the DirectIngestCloudTaskManager that runs tasks
    asynchronously on background threads."""

    def __init__(self) -> None:
        super().__init__()
        self.scheduler_queue = SingleThreadTaskQueue(name="scheduler")
        self.process_job_queue = SingleThreadTaskQueue(name="process_job")
        self.ingest_view_export_queue = SingleThreadTaskQueue(name="ingest_view_export")
        self.raw_data_import_queue = SingleThreadTaskQueue(name="raw_data_import")
        self.sftp_queue = SingleThreadTaskQueue(name="sftp")

    def create_direct_ingest_process_job_task(
        self,
        region: Region,
        ingest_args: LegacyExtractAndMergeArgs,
    ) -> None:
        if not self.controller:
            raise ValueError("Controller is null - did you call set_controller()?")

        task_id = build_process_job_task_id(region, ingest_args)
        self.process_job_queue.add_task(
            f"projects/path/to/{task_id}",
            with_monitoring(
                region.region_code,
                ingest_args.ingest_instance(),
                self.controller.run_extract_and_merge_job_and_kick_scheduler_on_completion,
            ),
            ingest_args,
        )

    def create_direct_ingest_scheduler_queue_task(
        self,
        region: Region,
        ingest_bucket: GcsfsBucketPath,
        just_finished_job: bool,
    ) -> None:
        if not self.controller:
            raise ValueError("Controller is null - did you call set_controller()?")
        if not self.controller.ingest_bucket_path == ingest_bucket:
            raise ValueError(
                f"Task request for ingest bucket [{ingest_bucket}] that does not match "
                f"registered controller ingest bucket [{self.controller.ingest_bucket_path}]."
            )

        ingest_instance = DirectIngestInstanceFactory.for_ingest_bucket(ingest_bucket)
        task_id = build_scheduler_task_id(region, ingest_instance)
        self.scheduler_queue.add_task(
            f"projects/path/to/{task_id}",
            with_monitoring(
                region.region_code,
                ingest_instance,
                self.controller.schedule_next_ingest_task,
            ),
            current_task_id=task_id,
            just_finished_job=just_finished_job,
        )

    def create_direct_ingest_handle_new_files_task(
        self,
        region: Region,
        ingest_bucket: GcsfsBucketPath,
        can_start_ingest: bool,
    ) -> None:
        if not self.controller:
            raise ValueError("Controller is null - did you call set_controller()?")
        if not self.controller.ingest_bucket_path == ingest_bucket:
            raise ValueError(
                f"Task request for ingest bucket [{ingest_bucket}] that does not match "
                f"registered controller ingest bucket [{self.controller.ingest_bucket_path}]."
            )

        ingest_instance = DirectIngestInstanceFactory.for_ingest_bucket(ingest_bucket)
        task_id = build_handle_new_files_task_id(region, ingest_instance)

        self.scheduler_queue.add_task(
            f"projects/path/to/{task_id}",
            with_monitoring(
                region.region_code,
                DirectIngestInstanceFactory.for_ingest_bucket(ingest_bucket),
                self.controller.handle_new_files,
            ),
            current_task_id=task_id,
            can_start_ingest=can_start_ingest,
        )

    def create_direct_ingest_raw_data_import_task(
        self,
        region: Region,
        data_import_args: GcsfsRawDataBQImportArgs,
    ) -> None:
        if not self.controller:
            raise ValueError("Controller is null - did you call set_controller()?")

        task_id = build_raw_data_import_task_id(region, data_import_args)
        self.raw_data_import_queue.add_task(
            f"projects/path/to/{task_id}",
            with_monitoring(
                region.region_code,
                data_import_args.ingest_instance(),
                self.controller.do_raw_data_import,
            ),
            data_import_args,
        )

    def create_direct_ingest_ingest_view_export_task(
        self,
        region: Region,
        ingest_view_export_args: GcsfsIngestViewExportArgs,
    ) -> None:
        if not self.controller:
            raise ValueError("Controller is null - did you call set_controller()?")

        task_id = build_ingest_view_export_task_id(region, ingest_view_export_args)
        self.ingest_view_export_queue.add_task(
            f"projects/path/to/{task_id}",
            with_monitoring(
                region.region_code,
                ingest_view_export_args.ingest_instance(),
                self.controller.do_ingest_view_export,
            ),
            ingest_view_export_args,
        )

    def create_direct_ingest_sftp_download_task(self, region: Region) -> None:
        task_id = build_sftp_download_task_id(region)
        self.sftp_queue.add_task(f"projects/path/to/{task_id}", lambda _: None)

    def delete_scheduler_queue_task(
        self, region: Region, ingest_instance: DirectIngestInstance, task_name: str
    ) -> None:
        self.scheduler_queue.delete_task(task_name)

    def get_process_job_queue_info(
        self, region: Region, ingest_instance: DirectIngestInstance
    ) -> ProcessIngestJobCloudTaskQueueInfo:
        with self.process_job_queue.all_tasks_mutex:
            task_names = self.process_job_queue.get_unfinished_task_names_unsafe()

        return ProcessIngestJobCloudTaskQueueInfo(
            queue_name=self.process_job_queue.name, task_names=task_names
        )

    def get_scheduler_queue_info(
        self, region: Region, ingest_instance: DirectIngestInstance
    ) -> SchedulerCloudTaskQueueInfo:
        with self.scheduler_queue.all_tasks_mutex:
            task_names = self.scheduler_queue.get_unfinished_task_names_unsafe()

        return SchedulerCloudTaskQueueInfo(
            queue_name=self.scheduler_queue.name, task_names=task_names
        )

    def get_raw_data_import_queue_info(
        self, region: Region
    ) -> RawDataImportCloudTaskQueueInfo:
        with self.raw_data_import_queue.all_tasks_mutex:
            task_names = self.raw_data_import_queue.get_unfinished_task_names_unsafe()

        return RawDataImportCloudTaskQueueInfo(
            queue_name=self.raw_data_import_queue.name, task_names=task_names
        )

    def get_ingest_view_export_queue_info(
        self, region: Region, ingest_instance: DirectIngestInstance
    ) -> IngestViewExportCloudTaskQueueInfo:
        with self.ingest_view_export_queue.all_tasks_mutex:
            task_names = (
                self.ingest_view_export_queue.get_unfinished_task_names_unsafe()
            )

        return IngestViewExportCloudTaskQueueInfo(
            queue_name=self.ingest_view_export_queue.name, task_names=task_names
        )

    def get_sftp_queue_info(self, region: Region) -> SftpCloudTaskQueueInfo:
        with self.sftp_queue.all_tasks_mutex:
            has_unfinished_tasks = self.sftp_queue.get_unfinished_task_names_unsafe()

        task_names = (
            [f"{region.region_code}-sftp-download"] if has_unfinished_tasks else []
        )
        return SftpCloudTaskQueueInfo(
            queue_name=self.sftp_queue.name, task_names=task_names
        )

    def wait_for_all_tasks_to_run(self) -> None:
        raw_data_import_done = False
        ingest_view_export_done = False
        scheduler_done = False
        process_job_queue_done = False
        while not (
            ingest_view_export_done
            and scheduler_done
            and process_job_queue_done
            and raw_data_import_done
        ):
            self.raw_data_import_queue.join()
            self.ingest_view_export_queue.join()
            self.scheduler_queue.join()
            self.process_job_queue.join()

            with self.ingest_view_export_queue.all_tasks_mutex:
                with self.scheduler_queue.all_tasks_mutex:
                    with self.process_job_queue.all_tasks_mutex:
                        raw_data_import_done = (
                            not self.raw_data_import_queue.get_unfinished_task_names_unsafe()
                        )
                        ingest_view_export_done = (
                            not self.ingest_view_export_queue.get_unfinished_task_names_unsafe()
                        )
                        scheduler_done = (
                            not self.scheduler_queue.get_unfinished_task_names_unsafe()
                        )
                        process_job_queue_done = (
                            not self.process_job_queue.get_unfinished_task_names_unsafe()
                        )