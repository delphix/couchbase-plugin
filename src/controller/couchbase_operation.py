#
# Copyright (c) 2020-2024 by Delphix. All rights reserved.
#

##############################################################################
"""
This class defines methods for couchbase operations. Parent classes are:
_BucketMixin, _ClusterMixin,
 _XDCrMixin, _CBBackupMixin. Modules name is explaining about the operations
 for which module is created for.
The constructor of this class expects a `builder` on which each database
operation will be performed
Commands are defined for each method in module commands.py. To perform any
delphix operation we need to create
the object of this class. This class is single connector between other modules
and `controller` package
"""
##############################################################################

import json
import logging
import os
import re
import time

from controller import helper_lib
from controller.couchbase_lib._bucket import _BucketMixin
from controller.couchbase_lib._cb_backup import _CBBackupMixin
from controller.couchbase_lib._cluster import _ClusterMixin
from controller.couchbase_lib._xdcr import _XDCrMixin
from controller.helper_lib import remap_bucket_json
from controller.resource_builder import Resource
from db_commands import constants
from db_commands.commands import CommandFactory
from db_commands.constants import CONFIG_FILE_NAME
from db_commands.constants import DELPHIX_HIDDEN_FOLDER
from db_commands.constants import StatusIsActive
from dlpx.virtualization.platform import Status
from dlpx.virtualization.platform.exceptions import UserError
from internal_exceptions.database_exceptions import CouchbaseServicesError
from utils import utilities

logger = logging.getLogger(__name__)


class CouchbaseOperation(
    _BucketMixin, _ClusterMixin, _XDCrMixin, _CBBackupMixin
):
    def __init__(self, builder, node_connection=None):
        """
        Main class through which other modules can run databases operations on
        provided parameters
        :param builder: builder object which contains all necessary parameters
        on which db methods will be executed
        :param node_connection: connection to node, if this is not a default
        one
        """

        logger.debug("Object initialization")
        # Initializing the parent class constructor
        super(CouchbaseOperation, self).__init__(builder)

        if node_connection is not None:
            self.connection = node_connection

        self.__need_sudo = helper_lib.need_sudo(
            self.connection, self.repository.uid, self.repository.gid
        )
        self.__uid = self.repository.uid
        self.__gid = self.repository.gid

    @property
    def need_sudo(self):
        return self.__need_sudo

    @property
    def uid(self):
        return self.__uid

    @property
    def gid(self):
        return self.__gid

    def run_couchbase_command(self, couchbase_command, **kwargs):
        logger.debug("run_couchbase_command")
        logger.debug("couchbase_command: {}".format(couchbase_command))
        if "password" in kwargs:
            password = kwargs.get("password")
        else:
            password = self.parameters.couchbase_admin_password
            kwargs["password"] = password

        if "username" in kwargs:
            username = kwargs.pop("username")
        else:
            username = self.parameters.couchbase_admin

        if "hostname" in kwargs:
            hostname = kwargs.pop("hostname")
        else:
            hostname = self.connection.environment.host.name

        if "port" in kwargs:
            port = kwargs.pop("port")
        else:
            port = self.parameters.couchbase_port

        env = {"password": password}

        if "newpass" in kwargs:
            # for setting a new password
            env["newpass"] = kwargs.get("newpass")

        if "source_password" in kwargs:
            env["source_password"] = kwargs.get("source_password")

        autoparams = [
            "shell_path",
            "install_path",
            "username",
            "port",
            "sudo",
            "uid",
            "hostname",
        ]

        new_kwargs = {k: v for k, v in kwargs.items() if k not in autoparams}
        if couchbase_command not in [
            "get_server_list",
            "couchbase_server_info",
            "cb_backup_full",
            "build_index",
            "check_index_build",
            "get_source_bucket_list",
            "get_replication_uuid",
            "get_stream_id",
            "delete_replication",
            "node_init",
            "get_indexes_name",
            "rename_cluster",
            "server_add",
            "rebalance",
            "get_scope_list_expect",
            "change_cluster_password",
            "create_scope_expect",
            "create_collection_expect",
        ]:
            method_to_call = getattr(CommandFactory, couchbase_command)
            command = method_to_call(
                shell_path=self.repository.cb_shell_path,
                install_path=self.repository.cb_install_path,
                username=username,
                port=port,
                sudo=self.need_sudo,
                uid=self.uid,
                hostname=hostname,
                **new_kwargs,
            )

            logger.debug("couchbase command to run: {}".format(command))
            stdout, stderr, exit_code = utilities.execute_bash(
                self.connection, command, environment_vars=env
            )
        else:
            couchbase_command = (
                couchbase_command + "_expect"
                if not couchbase_command.endswith("_expect")
                else couchbase_command
            )
            logger.debug("new_couchbase_command: {}".format(couchbase_command))
            method_to_call = getattr(CommandFactory, couchbase_command)
            command, env_vars = method_to_call(
                shell_path=self.repository.cb_shell_path,
                install_path=self.repository.cb_install_path,
                username=username,
                port=port,
                sudo=self.need_sudo,
                uid=self.uid,
                hostname=hostname,
                **new_kwargs,
            )
            env.update(env_vars)
            logger.debug("couchbase command to run: {}".format(command))
            stdout, stderr, exit_code = utilities.execute_expect(
                self.connection, command, environment_vars=env
            )
        return [stdout, stderr, exit_code]

    def run_os_command(self, os_command, **kwargs):

        method_to_call = getattr(CommandFactory, os_command)
        command = method_to_call(sudo=self.need_sudo, uid=self.uid, **kwargs)

        logger.debug("os command to run: {}".format(command))
        stdout, stderr, exit_code = utilities.execute_bash(
            self.connection, command
        )
        logger.debug(f"os_command stdout: {stdout}")
        logger.debug(f"os_command stderr: {stderr}")
        logger.debug(f"os_command exit_code: {exit_code}")
        return [stdout, stderr, exit_code]

    def restart_couchbase(self, provision=False):
        """stop the couchbase service and then start again"""
        self.stop_couchbase()
        self.start_couchbase(provision)

    def start_couchbase(self, provision=False, no_wait=False):
        """start the couchbase service"""
        logger.debug("Starting couchbase services")

        self.run_couchbase_command("start_couchbase")
        server_status = Status.INACTIVE

        helper_lib.sleepForSecond(10)

        if no_wait:
            logger.debug("no wait - leaving start procedure")
            return

        # Waiting for one minute to start the server
        # for prox to investigate
        end_time = time.time() + 3660

        # break the loop either end_time is exceeding from 1 minute or server
        # is successfully started
        while time.time() < end_time and server_status == Status.INACTIVE:
            helper_lib.sleepForSecond(1)  # waiting for 1 second
            server_status = self.status(provision)  # fetching status
            logger.debug("server status {}".format(server_status))

        # if the server is not running even in 60 seconds, then stop the
        # further execution
        if server_status == Status.INACTIVE:
            raise CouchbaseServicesError(
                "Have failed to start couchbase server"
            )

    def stop_couchbase(self):
        """stop the couchbase service"""
        try:
            logger.debug("Stopping couchbase services")
            self.run_couchbase_command("stop_couchbase")

            end_time = time.time() + 60
            server_status = Status.ACTIVE
            while time.time() < end_time and server_status == Status.ACTIVE:
                helper_lib.sleepForSecond(1)  # waiting for 1 second
                server_status = self.status()  # fetching status

            logger.debug("Leaving stop loop")
            if server_status == Status.ACTIVE:
                logger.debug("Have failed to stop couchbase server")
                raise CouchbaseServicesError(
                    "Have failed to stop couchbase server"
                )
        except CouchbaseServicesError as err:
            logger.debug("Error: {}".format(err))
            raise err
        except Exception as err:
            logger.debug("Exception Error: {}".format(err))
            if self.status() == Status.INACTIVE:
                logger.debug(
                    "Seems like couchbase service is not running. {}".format(
                        str(err)
                    )
                )
            else:
                raise CouchbaseServicesError(str(err))

    def ip_file_name(self):

        ip_file = "{}/../var/lib/couchbase/ip".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        check_ip_file, check_ip_file_err, exit_code = self.run_os_command(
            os_command="check_file", file_path=ip_file
        )

        if not (exit_code == 0 and "Found" in check_ip_file):
            ip_file = "{}/../var/lib/couchbase/ip_start".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )

        logger.debug("IP file is {}".format(ip_file))
        return ip_file

    def staging_bootstrap_status(self):
        logger.debug("staging_bootstrap_status")

        try:

            server_info_out, std_err, exit_code = self.run_couchbase_command(
                couchbase_command="couchbase_server_info", hostname="127.0.0.1"
            )

            # logger.debug("Status output: {}".format(server_info))

            status = helper_lib.get_value_of_key_from_json(
                server_info_out, "status"
            )
            if status.strip() == StatusIsActive:
                logger.debug("Server status is:  {}".format("ACTIVE"))
                return Status.ACTIVE
            else:
                logger.debug("Server status is:  {}".format("INACTIVE"))
                return Status.INACTIVE

        except Exception as error:
            # TODO
            # rewrite it
            logger.debug("Exception: {}".format(str(error)))
            if re.search("Unable to connect to host at", str(error)):
                logger.debug("Couchbase service is not running")
            return Status.INACTIVE

    def status(self, provision=False):
        """Check the server status. Healthy or Warmup could be one status
        if the server is running"""

        logger.debug("checking status")
        logger.debug(self.connection)
        try:

            if provision:
                username = self.snapshot.couchbase_admin
                password = self.snapshot.couchbase_admin_password

            else:
                password = self.parameters.couchbase_admin_password
                username = self.parameters.couchbase_admin

            # TODO
            # Check if there is a mount point - even a started Couchbase
            # without mountpoint means VDB
            # is down or corrupted
            # Couchbase with config file can start and recreate empty buckets
            # if there is no mount point
            # for future version - maybe whole /opt/couchbase/var directory
            # should be virtualized like for Docker
            # to avoid problems

            logger.debug("Checking for mount points")
            mount_point_state = helper_lib.check_server_is_used(
                self.connection, self.parameters.mount_path
            )
            logger.debug("Status of mount point {}".format(mount_point_state))

            if mount_point_state == Status.INACTIVE:
                logger.error(
                    "There is no mount point VDB is down regardless "
                    "Couchbase status"
                )
                return Status.INACTIVE

            ip_file = self.ip_file_name()

            read_ip_file, std_err, exit_code = self.run_os_command(
                os_command="cat", path=ip_file
            )

            server_info, std_err, exit_code = self.run_couchbase_command(
                couchbase_command="get_server_list",
                hostname="127.0.0.1",
                username=username,
                password=password,
            )

            if (
                not self.dSource
                and self.parameters.node_list is not None
                and len(self.parameters.node_list) > 0
            ):
                multinode = True
            else:
                multinode = False

            for line in server_info.split("\n"):
                logger.debug("Checking line: {}".format(line))
                if read_ip_file in line:
                    logger.debug("Checking IP: {}".format(read_ip_file))
                    if "unhealthy" in line:
                        logger.error("We have unhealthy active node")
                        return Status.INACTIVE
                    if "healthy" in line:
                        logger.debug("We have healthy active node")
                        return Status.ACTIVE

                    if multinode and "warmup" in line:
                        logger.debug(
                            "We have starting mode in multinode cluster"
                        )
                        return Status.ACTIVE

            return Status.INACTIVE

        except Exception as error:
            # TODO
            # rewrite it
            logger.debug("Exception: {}".format(str(error)))
            if re.search("Unable to connect to host at", str(error)):
                logger.debug("Couchbase service is not running")
            return Status.INACTIVE

    def make_directory(self, directory_path, force_env_user=False):
        """
        Create a directory and set the permission level 775
        :param directory_path: The directory path
        :return: None
        """

        # TODO
        # add error handling for OS errors

        logger.debug("Creating Directory {} ".format(directory_path))

        command_output, std_err, exit_code = self.run_os_command(
            os_command="make_directory", directory_path=directory_path
        )

        logger.debug(
            "Changing permission of directory path {}".format(directory_path)
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="change_permission", path=directory_path
        )

        logger.debug("Changed the permission of directory")

    def check_stale_mountpoint(self, path):

        output, stderr, exit_code = self.run_os_command(
            os_command="df", path=path
        )
        if exit_code != 0:
            if "No such file or directory" in stderr:
                # this is actually OK
                return False
            else:
                logger.error(
                    "df retured error - stale mount point or other error"
                )
                logger.error(
                    "stdout: {} stderr: {} exit_code: {}".format(
                        output, stderr, exit_code
                    )
                )
                return True
        else:
            return False

    def get_db_size(self, path: str) -> str:
        """
        Get the size of the dataset.

        :param connection: Staging connection.
        :param path: Mount location corresponding to dataset

        :return: du command output.

        """
        logger.debug("Started db sizing")
        du_std, du_stderr, du_exit_code = self.run_os_command(
            os_command="du", mount_path=path
        )
        if du_exit_code != 0:
            logger.error("Unable to calculate the dataset size")
            logger.error(f"stderr: {du_stderr}")
            raise UserError(
                "Problem with measuring mounted file system",
                "Ask OS admin to check mount",
                du_stderr,
            )
        logger.debug(f"Completed db sizing {du_std}")
        return du_std

    def create_config_dir(self):
        """create and return the hidden folder directory with name 'delphix'"""

        # TODO
        # clean up error handling

        logger.debug("Finding toolkit Path...")
        bin_directory, std_err, exit_code = self.run_os_command(
            os_command="get_dlpx_bin"
        )

        if bin_directory is None or bin_directory == "":
            raise Exception("Failed to find the toolkit directory")
        # Toolkit directory tested on linux x86_64Bit is 6 level below jq path
        loop_var = 6
        while loop_var:
            bin_directory = os.path.dirname(bin_directory)
            loop_var = loop_var - 1
        logger.debug(f"bin_directory={bin_directory}")
        logger.debug(f"DELPHIX_HIDDEN_FOLDER={DELPHIX_HIDDEN_FOLDER}")
        dir_name = bin_directory + "/" + DELPHIX_HIDDEN_FOLDER
        if not helper_lib.check_dir_present(self.connection, dir_name):
            self.make_directory(dir_name, force_env_user=True)
        return dir_name

    def source_bucket_list(self):
        """
        return all buckets exist on source server. Also contains the
        information bucketType, ramQuota, ramUsed,
        numReplicas
        :return:
        """
        # See the bucket list on source server
        logger.debug(
            "Collecting bucket list information present on source server "
        )

        bucket_list, error, exit_code = self.run_couchbase_command(
            couchbase_command="get_source_bucket_list",
            source_hostname=self.source_config.couchbase_src_host,
            source_port=self.source_config.couchbase_src_port,
            source_username=self.staged_source.parameters.xdcr_admin,
            password=self.staged_source.parameters.xdcr_admin_password,
        )

        if bucket_list == "[]" or bucket_list is None:
            return []
        else:
            logger.debug("clean up json")
            bucket_list = bucket_list.replace("u'", "'")
            bucket_list = bucket_list.replace("'", '"')
            bucket_list = bucket_list.replace("True", '"True"')
            bucket_list = bucket_list.replace("False", '"False"')
            logger.debug("parse json")
            bucket_list_dict = json.loads(bucket_list)
            bucket_list_dict = list(
                map(helper_lib.remap_bucket_json, bucket_list_dict)
            )

        logger.debug("Source Bucket Information {}".format(bucket_list_dict))
        return bucket_list_dict

    def get_backup_date(self, x):
        w = x.replace(
            "{}/{}/{}".format(
                self.parameters.couchbase_bak_loc,
                self.parameters.archive_name,
                self.parameters.couchbase_bak_repo,
            ),
            "",
        )
        g = re.match(r"/(.+?)/.*", w)
        if g:
            return g.group(1)
        else:
            return ""

    def source_bucket_list_offline(self):
        """
        This function will be used in CB backup manager. It will return the
        same output as by
        source_bucket_list method. To avoid source/production server dependency
         this function will be used.
        In a file, put all the bucket related information of source server.
        This function will cat and return the
        contents of that file. It is useful for cb backup manager ingestion
        mechanism
        FilePath : <Toolkit-Directory-Path>/couchbase_src_bucket_info
        In this file add output of below command:
        /opt/couchbase/bin/couchbase-cli bucket-list --cluster
        <sourcehost>:8091  --username $username --password $pass
        From here all source bucket list information we can fetch and other
        related data of this bucket should be placed
        at backup location.
        :param filename: filename(couchbase_src_bucket_info.cfg) where bucket
        information is kept.
        :return: bucket list information
        """

        logger.debug(self.parameters.couchbase_bak_loc)
        logger.debug(self.parameters.couchbase_bak_repo)

        bucket_list, error, exit_code = self.run_os_command(
            os_command="get_backup_bucket_list",
            path=os.path.join(
                self.parameters.couchbase_bak_loc,
                self.parameters.archive_name,
                self.parameters.couchbase_bak_repo,
            ),
        )

        backup_list = bucket_list.split("\n")
        logger.debug("Bucket search output: {}".format(backup_list))
        date_list = list(map(self.get_backup_date, backup_list))
        date_list.sort()
        logger.debug("date list: {}".format(date_list))
        files_to_process = [x for x in backup_list if date_list[-1] in x]

        logger.debug(files_to_process)

        bucket_list_dict = []

        for f in files_to_process:

            bucket_file_content, error, exit_code = self.run_os_command(
                os_command="cat", path=f
            )

            logger.debug(bucket_file_content)
            bucket_json = json.loads(bucket_file_content)
            bucket_list_dict.append(remap_bucket_json(bucket_json))

        logger.debug("Bucket search output: {}".format(bucket_list_dict))
        return bucket_list_dict

    def node_init(self, nodeno=1):
        """
        This method initializes couchbase server node. Where user sets
        different required paths
        :return: None
        """
        logger.debug("Initializing the NODE")

        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="node_init",
            data_path="{}/data_{}".format(self.parameters.mount_path, nodeno),
        )

        logger.debug("Command Output {} ".format(command_output))

    def get_config_directory(self):
        """
        Hidden directory path inside mount directory will be returned. which
        is created in method create_config_dir
        :return: Return the config directory
        """

        config_path = self.parameters.mount_path + "/" + DELPHIX_HIDDEN_FOLDER
        logger.debug("Config folder is: {}".format(config_path))
        return config_path

    def get_config_file_path(self):
        """
        :return: Config file created inside the hidden folder.
        """
        config_file_path = self.get_config_directory() + "/" + CONFIG_FILE_NAME
        logger.debug("Config filepath is: {}".format(config_file_path))
        return config_file_path

    # Defined for future updates
    def get_indexes_definition(self):
        # by default take from staging but later take from source
        logger.debug("Finding indexes....")
        password = self.parameters.couchbase_admin_password
        user = self.parameters.couchbase_admin
        port = self.parameters.couchbase_port
        if self.dSource:
            if self.parameters.d_source_type == constants.CBBKPMGR:
                hostname = self.parameters.couchbase_host
            else:
                port = self.source_config.couchbase_src_port
                user = self.staged_source.parameters.xdcr_admin
                password = self.staged_source.parameters.xdcr_admin_password
                hostname = self.source_config.couchbase_src_host
        else:
            hostname = self.connection.environment.host.name

        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="get_indexes_name",
            hostname=hostname,
            username=user,
            port=port,
            password=password,
        )

        logger.debug("Indexes are {}".format(command_output))
        indexes_raw = json.loads(command_output)
        indexes = []

        logger.debug(
            "dSource type for indexes: {}".format(
                self.parameters.d_source_type
            )
        )

        if self.parameters.d_source_type == constants.CBBKPMGR:
            logger.debug("Only build for backup ingestion")
            buckets = {}
            for i in indexes_raw["indexes"]:
                bucket_name = i["bucket"]
                index_name = i["indexName"]
                scope_name = i["scope"] if "scope" in i.keys() else "_default"
                collection_name = (
                    i["collection"] if "collection" in i.keys() else "_default"
                )

                if bucket_name not in buckets:
                    buckets[bucket_name] = {}
                if scope_name not in buckets[bucket_name].keys():
                    buckets[bucket_name][scope_name] = {}
                if (
                    collection_name
                    not in buckets[bucket_name][scope_name].keys()
                ):
                    buckets[bucket_name][scope_name][collection_name] = []

                buckets[bucket_name][scope_name][collection_name].append(
                    index_name
                )

            for bucket_name in buckets.keys():
                for scope_name in buckets[bucket_name].keys():
                    for collection_name in buckets[bucket_name][
                        scope_name
                    ].keys():
                        ind = buckets[bucket_name][scope_name][collection_name]
                        if (
                            collection_name == "_default"
                            and scope_name == "_default"
                        ):
                            ind_def = (
                                f"build index on `{bucket_name}` "
                                f'(`{"`,`".join(ind)}`)'
                            )
                        else:
                            ind_def = (
                                f"build index on `{bucket_name}`."
                                f"{scope_name}.{collection_name} "
                                f'(`{"`,`".join(ind)}`)'
                            )
                        indexes.append(ind_def)

        else:
            # full definition for replication

            for i in indexes_raw["indexes"]:
                indexes.append(
                    i["definition"].replace(
                        'defer_build":true', 'defer_build":false'
                    )
                )
        return indexes

    # Defined for future updates
    def build_index(self, index_def):
        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="build_index",
            base_path=helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            ),
            index_def=index_def,
        )

        logger.debug("command_output is {}".format(command_output))
        return command_output

    def check_index_build(self):
        # set timeout to 12 hours
        end_time = time.time() + 3660 * 12

        tobuild = 1

        # break the loop either end_time is exceeding from 1 minute or server
        # is successfully started
        while time.time() < end_time and tobuild != 0:

            command_output, std_err, exit_code = self.run_couchbase_command(
                couchbase_command="check_index_build",
                base_path=helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                ),
            )

            logger.debug("command_output is {}".format(command_output))
            logger.debug("std_err is {}".format(std_err))
            logger.debug("exit_code is {}".format(exit_code))
            try:
                command_output_dict = json.loads(command_output)
                logger.debug("dict {}".format(command_output_dict))
                tobuild = command_output_dict["results"][0]["unbuilt"]
                logger.debug("to_build is {}".format(tobuild))
                helper_lib.sleepForSecond(30)  # waiting for 1 second
            except Exception as e:
                logger.debug(str(e))

    def save_config(self, what, nodeno=1):

        # TODO
        # Error handling

        logger.debug("start save_config")

        targetdir = self.get_config_directory()
        target_config_filename = os.path.join(
            targetdir, "config.dat_{}".format(nodeno)
        )
        target_local_filename = os.path.join(
            targetdir, "local.ini_{}".format(nodeno)
        )
        target_encryption_filename = os.path.join(
            targetdir, "encrypted_data_keys_{}".format(nodeno)
        )

        if nodeno == 1 or int(self.repository.version.split(".")[0]) >= 7:
            ip_file = "{}/../var/lib/couchbase/ip".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )
            target_ip_filename = os.path.join(
                targetdir, "ip_{}".format(nodeno)
            )
            output, err, exit_code = self.run_os_command(
                os_command="check_file", file_path=ip_file
            )
            if exit_code != 0 and "Found" not in output:
                ip_file = "{}/../var/lib/couchbase/ip_start".format(
                    helper_lib.get_base_directory_of_given_path(
                        self.repository.cb_shell_path
                    )
                )
                target_ip_filename = os.path.join(
                    targetdir, "ip_start_{}".format(nodeno)
                )
        else:
            ip_file = "{}/../var/lib/couchbase/ip_start".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )
            target_ip_filename = os.path.join(
                targetdir, "ip_start_{}".format(nodeno)
            )

        filename = "{}/../var/lib/couchbase/config/config.dat".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_cp",
            srcname=filename,
            trgname=target_config_filename,
        )

        logger.debug(
            "save config.dat cp - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

        if exit_code != 0:
            raise UserError(
                "Error saving configuration file: config.dat",
                "Check sudo or user privileges to read Couchbase config.dat "
                "file",
                std_err,
            )

        # encryption data keys may not exist on Community edition

        filename = "{}/../var/lib/couchbase/config/encrypted_data_keys".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        (
            check_encrypted_data_keys,
            check_ip_file_err,
            exit_code,
        ) = self.run_os_command(os_command="check_file", file_path=filename)

        if exit_code == 0 and "Found" in check_encrypted_data_keys:
            command_output, std_err, exit_code = self.run_os_command(
                os_command="os_cp",
                srcname=filename,
                trgname=target_encryption_filename,
            )

            logger.debug(
                "save encrypted_data_keys.dat cp - exit_code: {} stdout: {} "
                "std_err: {}".format(exit_code, command_output, std_err)
            )
            if exit_code != 0:
                raise UserError(
                    "Error saving configuration file: encrypted_data_keys",
                    "Check sudo or user privileges to read Couchbase "
                    "encrypted_data_keys file",
                    std_err,
                )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_cp", srcname=ip_file, trgname=target_ip_filename
        )

        logger.debug(
            "save {} - exit_code: {} stdout: {} std_err: {}".format(
                ip_file, exit_code, command_output, std_err
            )
        )

        if exit_code != 0:
            raise UserError(
                "Error saving configuration file: {}".format(ip_file),
                "Check sudo or user privileges to read Couchbase "
                "{} file".format(ip_file),
                std_err,
            )

        filename = "{}/../etc/couchdb/local.ini".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_cp", srcname=filename, trgname=target_local_filename
        )

        logger.debug(
            "save local.ini cp - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )
        if exit_code != 0:
            raise UserError(
                "Error saving configuration file: local.ini",
                "Check sudo or user privileges to read Couchbase local.ini "
                "file",
                std_err,
            )

        if int(self.repository.version.split(".")[0]) >= 7:
            chronicle_target_dir = os.path.join(
                targetdir, f"chronicle_{nodeno}"
            )
            (
                chronicle_target_dir_command_output,
                _,
                chronicle_target_dir_exit_code,
            ) = self.run_os_command(
                os_command="check_directory", dir_path=chronicle_target_dir
            )
            if (
                chronicle_target_dir_exit_code == 0
                and "Found" in chronicle_target_dir_command_output
            ):
                self.run_os_command(
                    os_command="delete_dir", dirname=chronicle_target_dir
                )
            self.run_os_command(
                os_command="os_cpr",
                srcname="{}/../var/lib/couchbase/config/chronicle".format(
                    helper_lib.get_base_directory_of_given_path(
                        self.repository.cb_shell_path
                    )
                ),
                trgname=chronicle_target_dir,
            )
        if (
            hasattr(self.parameters, "d_source_type")
            and self.parameters.d_source_type == constants.CBBKPMGR
        ):
            self.run_os_command(
                os_command="write_file",
                filename=os.path.join(
                    self.parameters.mount_path, ".delphix/backup_restore.txt"
                ),
                data=self.parameters.archive_name,
            )

    def check_cluster_notconfigured(self):

        logger.debug("check_cluster")

        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="get_server_list",
            hostname=self.connection.environment.host.name,
        )

        if "unknown pool" in command_output:
            return True
        else:
            return False

    def check_cluster_configured(self):

        logger.debug("check_cluster configured")

        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="get_server_list",
            hostname=self.connection.environment.host.name,
        )

        if "healthy active" in command_output:
            return True
        else:
            return False

    def check_config(self):

        filename = os.path.join(self.get_config_directory(), "config.dat")
        cmd = CommandFactory.check_file(filename)
        logger.debug("check file cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(
            self.connection, command_name=cmd, callback_func=self.ignore_err
        )

        if exit_code == 0 and "Found" in command_output:
            return True
        else:
            return False

    def delete_data_folder(self, nodeno=1):
        data_folder = "{}/data_{}".format(self.parameters.mount_path, nodeno)
        (
            command_output,
            command_stderr,
            command_exit_code,
        ) = self.run_os_command(
            os_command="check_directory", dir_path=data_folder
        )
        logger.debug(
            f"check data directory >> command_output=={command_output}"
            f" , command_stderr=={command_stderr} , "
            f"command_exit_code=={command_exit_code}"
        )
        if command_output == "Found":
            self.run_os_command(os_command="delete_dir", dirname=data_folder)

    def delete_config_folder(self):
        if int(self.repository.version.split(".")[0]) >= 6:
            config_directory_path = "{}/../var/lib/couchbase/config".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )
            (
                command_output,
                command_stderr,
                command_exit_code,
            ) = self.run_os_command(
                os_command="check_directory", dir_path=config_directory_path
            )
            logger.debug(
                f"check directory >> command_output=={command_output}"
                f" , command_stderr=={command_stderr} , "
                f"command_exit_code=={command_exit_code}"
            )
            if command_output == "Found":
                target_folder = f"{config_directory_path}_bkp"
                (
                    command_output,
                    command_stderr,
                    command_exit_code,
                ) = self.run_os_command(
                    os_command="check_directory", dir_path=target_folder
                )
                if command_output == "Found":
                    self.run_os_command(
                        os_command="delete_dir", dirname=target_folder
                    )
                self.run_os_command(
                    os_command="os_mv",
                    srcname=config_directory_path,
                    trgname=target_folder,
                )
                # logger.debug(
                #     f"mv directory >> command_output=={command_output}"
                #     f" , command_stderr=={command_stderr} , "
                #     f"command_exit_code=={command_exit_code}"
                # )

    def delete_xdcr_config(self):
        if self.parameters.d_source_type == "XDCR":
            is_xdcr_setup, cluster_name = self.delete_replication()
            if is_xdcr_setup:
                logger.info("Deleting XDCR")
                self.xdcr_delete(cluster_name)

    def restore_config(self, what, nodeno=1):

        # TODO
        # Error handling

        logger.debug("start restore_config")

        sourcedir = self.get_config_directory()

        source_config_file = os.path.join(
            sourcedir, "config.dat_{}".format(nodeno)
        )
        source_local_filename = os.path.join(
            sourcedir, "local.ini_{}".format(nodeno)
        )
        source_encryption_keys = os.path.join(
            sourcedir, "encrypted_data_keys_{}".format(nodeno)
        )

        source_ip_file = os.path.join(sourcedir, "ip_{}".format(nodeno))
        target_ip_file = "{}/../var/lib/couchbase/ip".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )
        delete_ip_file = "{}/../var/lib/couchbase/ip_start".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        check_ip_file, check_ip_file_err, exit_code = self.run_os_command(
            os_command="check_file", file_path=source_ip_file
        )

        if not (exit_code == 0 and "Found" in check_ip_file):
            source_ip_file = os.path.join(
                sourcedir, "ip_start_{}".format(nodeno)
            )
            target_ip_file = "{}/../var/lib/couchbase/ip_start".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )
            delete_ip_file = "{}/../var/lib/couchbase/ip".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )

        logger.debug("IP file is {}".format(source_ip_file))

        targetfile = "{}/../var/lib/couchbase/config/config.dat".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_cp", srcname=source_config_file, trgname=targetfile
        )

        logger.debug(
            "config.dat restore - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

        (
            check_encrypted_data_keys,
            check_ip_file_err,
            exit_code,
        ) = self.run_os_command(
            os_command="check_file", file_path=source_encryption_keys
        )

        logger.debug(
            "Check check_encrypted_data_keys - exit_code: {} "
            "stdout: {}".format(exit_code, check_encrypted_data_keys)
        )

        if exit_code == 0 and "Found" in check_encrypted_data_keys:
            targetfile = (
                "{}/../var/lib/couchbase/config/encrypted_data_keys".format(
                    helper_lib.get_base_directory_of_given_path(
                        self.repository.cb_shell_path
                    )
                )
            )
            command_output, std_err, exit_code = self.run_os_command(
                os_command="os_cp",
                srcname=source_encryption_keys,
                trgname=targetfile,
            )

            logger.debug(
                "encrypted_data_keys restore - exit_code: {} stdout: {} "
                "std_err: {}".format(exit_code, command_output, std_err)
            )

        (
            check_ip_delete_file,
            check_ip_delete_file,
            check_ip_exit_code,
        ) = self.run_os_command(
            os_command="check_file", file_path=delete_ip_file
        )

        logger.debug(
            "Check delete old ip_file - exit_code: {} stdout: {}".format(
                check_ip_exit_code, check_ip_delete_file
            )
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_mv",
            srcname=delete_ip_file,
            trgname="{}.bak".format(delete_ip_file),
        )

        logger.debug(
            "ipfile delete - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_cp", srcname=source_ip_file, trgname=target_ip_file
        )

        logger.debug(
            "ipfile restore - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

        targetfile = "{}/../etc/couchdb/local.ini".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="os_cp",
            srcname=source_local_filename,
            trgname=targetfile,
        )

        logger.debug(
            "local.ini restore - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

        if int(self.repository.version.split(".")[0]) >= 7:
            source_chronicle_dirname = os.path.join(
                sourcedir, "chronicle_{}".format(nodeno)
            )
            target_chronicle_dirname = (
                "{}/../var/lib/couchbase/config/chronicle".format(
                    helper_lib.get_base_directory_of_given_path(
                        self.repository.cb_shell_path
                    )
                )
            )
            command_output, std_err, exit_code = self.run_os_command(
                os_command="check_directory", dir_path=target_chronicle_dirname
            )
            if exit_code == 0 and "Found" in command_output:
                self.run_os_command(
                    os_command="delete_dir", dirname=target_chronicle_dirname
                )
            command_output, std_err, exit_code = self.run_os_command(
                os_command="os_cpr",
                srcname=source_chronicle_dirname,
                trgname=target_chronicle_dirname,
            )

        logger.debug(
            "chronicle restore - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

        if what == "parent":
            # local.ini needs to have a proper entry
            filename = "{}/../etc/couchdb/local.ini".format(
                helper_lib.get_base_directory_of_given_path(
                    self.repository.cb_shell_path
                )
            )
            newpath = "{}/data_{}".format(self.parameters.mount_path, nodeno)
            cmd = CommandFactory.sed(
                filename,
                "s|view_index_dir.*|view_index_dir={}|".format(newpath),
                self.need_sudo,
                self.uid,
            )
            logger.debug("sed config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(
                self.connection, command_name=cmd
            )
            logger.debug(
                "setting index paths - exit_code: {} stdout: {} "
                "std_err: {}".format(exit_code, command_output, std_err)
            )

            cmd = CommandFactory.sed(
                filename,
                "s|database_dir.*|database_dir={}|".format(newpath),
                self.need_sudo,
                self.uid,
            )
            logger.debug("sed config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(
                self.connection, command_name=cmd
            )
            logger.debug(
                "setting data paths - exit_code: {} stdout: {} "
                "std_err: {}".format(exit_code, command_output, std_err)
            )

    def delete_config(self):

        # TODO:
        # error handling

        logger.debug("start delete_config")

        filename = "{}/../var/lib/couchbase/config/config.dat".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )

        cmd = CommandFactory.check_file(filename, self.need_sudo, self.uid)
        logger.debug("check file cmd: {}".format(cmd))
        command_output, std_err, exit_code = utilities.execute_bash(
            self.connection, command_name=cmd, callback_func=self.ignore_err
        )

        if exit_code == 0 and "Found" in command_output:
            cmd = CommandFactory.os_mv(
                filename, "{}.bak".format(filename), self.need_sudo, self.uid
            )
            logger.debug("rename config cmd: {}".format(cmd))
            command_output, std_err, exit_code = utilities.execute_bash(
                self.connection, command_name=cmd
            )
            logger.debug(
                "rename config.dat to bak - exit_code: {} stdout: {} "
                "std_err: {}".format(exit_code, command_output, std_err)
            )

        filename = "{}/../etc/couchdb/local.ini".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )
        command_output, std_err, exit_code = self.run_os_command(
            os_command="sed", filename=filename, regex="s/view_index_dir.*//"
        )

        logger.debug(
            "clean local.ini index - exit_code: {} stdout: {} "
            "std_err: {}".format(exit_code, command_output, std_err)
        )

        command_output, std_err, exit_code = self.run_os_command(
            os_command="sed", filename=filename, regex="s/database_dir.*//"
        )

        logger.debug(
            "clean local.ini data - exit_code: {} stdout: {} "
            "std_err: {}".format(exit_code, command_output, std_err)
        )
        command_output, std_err, exit_code = self.run_os_command(
            os_command="change_permission", path=filename
        )

        logger.debug(
            "fix local.ini permission - exit_code: {} stdout: {} "
            "std_err: {}".format(exit_code, command_output, std_err)
        )

        chronicle_dir_name = "{}/../var/lib/couchbase/config/chronicle".format(
            helper_lib.get_base_directory_of_given_path(
                self.repository.cb_shell_path
            )
        )
        self.run_os_command(
            os_command="delete_dir", dirname=chronicle_dir_name
        )

    def ignore_err(self, input):
        return True

    def rename_cluster(self):
        """Rename cluster based on user entries"""

        logger.debug("start rename_cluster")
        self.run_couchbase_command(
            couchbase_command="rename_cluster",
            username=self.snapshot.couchbase_admin,
            password=self.snapshot.couchbase_admin_password,
            newname=self.parameters.tgt_cluster_name,
        )
        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="change_cluster_password",
            username=self.snapshot.couchbase_admin,
            password=self.snapshot.couchbase_admin_password,
            newuser=self.parameters.couchbase_admin,
            newpass=self.parameters.couchbase_admin_password,
        )

        logger.debug(
            "rename cluster - exit_code: {} stdout: {} std_err: {}".format(
                exit_code, command_output, std_err
            )
        )

    def start_node_bootstrap(self):
        logger.debug("start start_node_bootstrap")
        self.start_couchbase(no_wait=True)
        end_time = time.time() + 3660
        server_status = Status.INACTIVE

        # break the loop either end_time is exceeding from 1 minute or server
        # is successfully started
        while time.time() < end_time and server_status != Status.ACTIVE:
            helper_lib.sleepForSecond(1)  # waiting for 1 second
            server_status = self.staging_bootstrap_status()  # fetching status
            logger.debug("server status {}".format(server_status))

    def addnode(self, nodeno, node_def):
        logger.debug("start addnode")

        self.delete_config()

        self.start_node_bootstrap()

        self.node_init(nodeno)

        helper_lib.sleepForSecond(10)

        services = ["data", "index", "query"]

        if "fts_service" in node_def and node_def["fts_service"]:
            services.append("fts")

        if "eventing_service" in node_def and node_def["eventing_service"]:
            services.append("eventing")

        if "analytics_service" in node_def and node_def["analytics_service"]:
            services.append("analytics")

        logger.debug("services to add: {}".format(services))

        logger.debug("node host name / IP: {}".format(node_def["node_addr"]))

        resolve_name_command = CommandFactory.resolve_name(
            hostname=node_def["node_addr"]
        )
        logger.debug(
            "resolve_name_command command: {}".format(resolve_name_command)
        )
        resolve_name_output, std_err, exit_code = utilities.execute_bash(
            self.connection, resolve_name_command
        )
        logger.debug(
            "resolve_name_command Output {} ".format(resolve_name_output)
        )

        if int(self.repository.version.split(".")[0]) >= 7:
            if "(CE)" in self.repository.version:
                new_port = "8091"
            else:
                new_port = "18091"
        else:
            new_port = "18091"

        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="server_add",
            hostname=self.connection.environment.host.name,
            newhost=resolve_name_output,
            services=",".join(services),
            new_port=new_port,
        )

        logger.debug(
            "Add node Output {} stderr: {} exit_code: {} ".format(
                command_output, std_err, exit_code
            )
        )

        if exit_code != 0:
            logger.debug("Adding node error")
            raise UserError(
                "Problem with adding node",
                "Check an output and fix problem before retrying to provision "
                "a VDB",
                "stdout: {} stderr:{}".format(command_output, std_err),
            )

        command_output, std_err, exit_code = self.run_couchbase_command(
            couchbase_command="rebalance",
            hostname=self.connection.environment.host.name,
        )

        logger.debug(
            "Rebalance Output {} stderr: {} exit_code: {} ".format(
                command_output, std_err, exit_code
            )
        )

        if exit_code != 0:
            logger.debug("Rebalancing error")
            raise UserError(
                "Problem with rebalancing cluster",
                "Check an output and fix problem before retrying to provision "
                "a VDB",
                "stdout: {} stderr:{}".format(command_output, std_err),
            )


if __name__ == "__main__":
    # print "Checking Couchbase Class"
    test_object = CouchbaseOperation(
        Resource.ObjectBuilder.set_dsource(True).build()
    )
    print(test_object.get_config_file_path.__doc__)
