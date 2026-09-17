#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
"""This class contains methods for all cb backup manager.
This is child class of Resource and parent class of CouchbaseOperation.
"""
import json

##############################################################################
import logging
import os
from datetime import datetime

from controller import helper_lib
from controller.couchbase_lib._mixin_interface import MixinInterface
from controller.resource_builder import Resource
from dlpx.virtualization.platform.exceptions import UserError

logger = logging.getLogger(__name__)


class _CBBackupMixin(Resource, MixinInterface):
    def __init__(self, builder):
        super(_CBBackupMixin, self).__init__(builder)

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {
            "base_path": helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            ),
            "hostname": self.connection.environment.host.name,
            "port": self.parameters.couchbase_port,
            "username": self.parameters.couchbase_admin,
        }
        # MixinInterface.read_map(env)
        return env

    def check_and_update_archive_path(self, check_file=False):
        folder_name = self.parameters.archive_name
        if self.parameters.archive_name == "":
            command_output, std_err, exit_code = self.run_os_command(
                os_command="os_ls", dir_path=self.parameters.couchbase_bak_loc
            )
            logger.debug(f"command_output={command_output}")
            datetime_object_list = []
            for archive_name in command_output.split("\n"):
                # archive name in format 20230810010001
                try:
                    datetime_archive_name = datetime.strptime(
                        archive_name, "%Y%m%d%H%M%S"
                    )
                    datetime_object_list.append(datetime_archive_name)
                except ValueError:
                    logger.debug(
                        f"Cannot convert {archive_name} into "
                        f"%Y%m%d%H%M%S format."
                    )
            if not datetime_object_list:
                raise UserError(
                    f"No valid backups found in %Y%m%d%H%M%S "
                    f"format in directory "
                    f"{self.parameters.couchbase_bak_loc}."
                )
            else:
                max_date = max(datetime_object_list)
                folder_name = max_date.strftime("%Y%m%d%H%M%S")
                logger.debug(
                    f"maximum date = {max_date}, " f"folder_name={folder_name}"
                )
                file_data = ""
                if check_file:
                    backup_restore_filename = os.path.join(
                        self.parameters.mount_path,
                        ".delphix/backup_restore.txt",
                    )
                    check_file_stdout, _, exit_code = self.run_os_command(
                        os_command="check_file",
                        file_path=backup_restore_filename,
                    )

                    if exit_code == 0 and "Found" in check_file_stdout:
                        file_data, _, _ = self.run_os_command(
                            os_command="cat", path=backup_restore_filename
                        )
                        file_data = file_data.strip()

                if file_data == folder_name:
                    raise UserError("No new backups found....exiting snapshot")
                else:
                    self.parameters.archive_name = folder_name
        return folder_name

    def cb_backup_full(self, csv_bucket):
        logger.debug("Starting Restore via Backup file...")
        logger.debug("csv_bucket_list: {}".format(csv_bucket))

        skip = "--disable-analytics"

        if not self.parameters.fts_service:
            skip = skip + " {} {} ".format(
                "--disable-ft-indexes", "--disable-ft-alias"
            )

        if not self.parameters.eventing_service:
            skip = skip + " {} ".format("--disable-eventing")

        logger.debug("skip backup is set to: {}".format(skip))
        map_data_list = []
        if int(self.repository.version.split(".")[0]) >= 7:
            for bucket_name in csv_bucket.split(","):
                logger.debug(f"bucket_name: {bucket_name}")
                stdout, _, _ = self.run_couchbase_command(
                    couchbase_command="get_scope_list_expect",
                    base_path=helper_lib.get_base_directory_of_given_path(
                        self.repository.cb_shell_path
                    ),
                    bucket_name=bucket_name,
                )
                json_scope_data = json.loads(stdout)
                for s in json_scope_data["scopes"]:
                    scope_name = s["name"]
                    if scope_name == "_default":
                        continue
                    collection_list = s["collections"]
                    for c in collection_list:
                        collection_name = c["name"]
                        if collection_name == "_default":
                            continue
                        map_data_list.append(
                            f"{bucket_name}.{scope_name}.{collection_name}="
                            f"{bucket_name}.{scope_name}.{collection_name}"
                        )

        stdout, stderr, exit_code = self.run_couchbase_command(
            couchbase_command="cb_backup_full",
            backup_location=os.path.join(
                self.parameters.couchbase_bak_loc, self.parameters.archive_name
            ),
            csv_bucket_list=csv_bucket,
            backup_repo=self.parameters.couchbase_bak_repo,
            skip=skip,
            base_path=helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            ),
            map_data=",".join(map_data_list),
            repo_version=self.repository.version,
        )

        if exit_code != 0:
            raise UserError(
                "Problem with restoring backup using cbbackupmgr",
                "Check if repo and all privileges are correct",
                "stdout: {}, stderr: {}, exit_code: {}".format(
                    stdout, stderr, exit_code
                ),
            )
