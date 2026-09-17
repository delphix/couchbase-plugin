#
# Copyright (c) 2020-2024 by Delphix. All rights reserved.
#

##############################################################################
"""
 This module contains common functionality that is being used across plugin.
 Like bucket size calculation, read file, write data into file and also
 operations required in discovery.
 Moreover it helps in colorful logging in debug log. Recommending to view the
 logs using the tail command then easily segregate the
 running command/output/exception/debug
 messages.

"""
##############################################################################

import json
import logging
import os
import os.path
import random
import re
import time
from datetime import datetime

import db_commands
from db_commands.commands import CommandFactory
from db_commands.constants import DEFAULT_CB_BIN_PATH
from dlpx.virtualization.platform import Status
from dlpx.virtualization.platform.exceptions import UserError
from internal_exceptions.plugin_exceptions import FileIOError
from internal_exceptions.plugin_exceptions import RepositoryDiscoveryError
from internal_exceptions.plugin_exceptions import SourceConfigDiscoveryError
from internal_exceptions.plugin_exceptions import UnmountFileSystemError
from utils import utilities

# Global logger object for this file
logger = logging.getLogger(__name__)


def find_binary_path(source_connection):
    """
    :param source_connection: Connection for the source environment
    :return: Bin path defined in environment variable '$COUCHBASE_PATH'.
    If it is not defined then "/opt/couchbase/bin"
    """
    logger.debug("Finding Binary Path...")
    binary_paths, std_err, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.find_binary_path()
    )
    if binary_paths == "":
        logger.debug(
            "Please verify COUCHBASE_PATH is defined. Checking at default "
            "location {}".format(DEFAULT_CB_BIN_PATH)
        )
        binary_paths = DEFAULT_CB_BIN_PATH
    else:
        logger.debug(
            "List of couchbase path found are {}".format(
                binary_paths.split(";")
            )
        )
    logger.debug("Finding Binary: {}".format(binary_paths))
    return binary_paths


def find_shell_path(source_connection, binary_path):
    """
    :param source_connection:Connection for the source environment
    :param binary_path: Couchbase binary path
    :return:path of cluster management utility: {couchbase-cli}
    """
    logger.debug("Finding Shell Path...")
    shell_path, std_err, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.find_shell_path(binary_path)
    )
    if shell_path == "":
        message = "Shell path {}/couchbase-cli not found".format(binary_path)
        raise RepositoryDiscoveryError(message)
    return shell_path


def find_install_path(source_connection, binary_path):
    """

    :param source_connection:Connection for the source environment
    :param binary_path: Couchbase binary path
    :return: path of couchbase-server, through which daemon processes can
    start in background
    """
    logger.debug("Finding install Path...")
    install_path, std_err, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.find_install_path(binary_path)
    )
    if install_path == "":
        message = "Install path {}/couchbase-server not found".format(
            binary_path
        )
        raise RepositoryDiscoveryError(message)
    else:
        logger.debug(
            "couchbase-server found in directory {}".format(install_path)
        )
    return install_path


def find_version(source_connection, install_path):
    """return the couchbase version installed on the host"""
    cb_version, std_err, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.get_version(install_path)
    )
    version = re.search(r"\d.*$", cb_version).group()
    logger.debug("Couchbase version installed {}".format(version))
    return version


def find_ids(source_connection, install_path):
    """return the couchbase uid and gid"""
    std_out, std_err, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.get_ids(install_path)
    )
    logger.debug("find ids output: {}".format(std_out))
    ids = re.search(r"[-rwx.]+\s\d\s([\d]+)\s([\d]+).*", std_out)
    if ids:
        uid = int(ids.group(1))
        gid = int(ids.group(2))
    else:
        uid = -1
        gid = -1
    logger.debug("Couchbase user uid {} gid {}".format(uid, gid))
    return (uid, gid)


def find_whoami(source_connection):
    """return the user env id"""
    std_out, std_err, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.whoami()
    )
    logger.debug("find whoami output: {}".format(std_out))
    ids = re.search(r"uid=([\d]+).*gid=([\d]+)", std_out)
    if ids:
        uid = int(ids.group(1))
        gid = int(ids.group(2))
    else:
        uid = -1
        gid = -1
    logger.debug("Delphix user uid {} gid {}".format(uid, gid))
    return (uid, gid)


def need_sudo(source_connection, couchbase_uid, couchbase_gid):
    (uid, gid) = find_whoami(source_connection)
    if uid != couchbase_uid or gid != couchbase_gid:
        return True
    else:
        return False


def is_instance_present_of_gosecrets(source_connection):
    """check couchbase server is running or not"""
    instance, stderr, exit_code = utilities.execute_bash(
        source_connection, CommandFactory.get_process()
    )
    # return true if 'gosecrets' string is present in output of get_process
    return "gosecrets" in instance


def get_data_directory(source_connection, repository):
    couchbase_install_path = repository.cb_install_path
    couchbase_binary_path = os.path.dirname(couchbase_install_path)
    couchbase_base_dir = os.path.dirname(couchbase_binary_path)
    filename = "{}/etc/couchbase/static_config".format(couchbase_base_dir)
    static_config, stderr, exit_code = read_file(source_connection, filename)
    if not re.search(
        r"(?<=path_config_datadir, \").*(?=\"}\.)", static_config
    ):
        message = "Cannot find data directory"
        logger.debug(message)
        raise SourceConfigDiscoveryError(message)
    data_directory = re.search(
        r"(?<=path_config_datadir, \").*(?=\"}\.)", static_config
    ).group()
    logger.debug("data_directory is {} ".format(data_directory))
    return data_directory


def get_base_directory_of_given_path(binary_path):
    """Return the base directory of given path"""
    path = os.path.split(binary_path)[0]
    return path


def remap_bucket_json(bucket):
    output = {}
    if "bucketType" in bucket:
        output["bucketType"] = bucket["bucketType"]
    if "name" in bucket:
        output["name"] = bucket["name"]
    if "quota" in bucket and "ram" in bucket["quota"]:
        output["ram"] = bucket["quota"]["ram"]
    elif "ramQuota" in bucket:
        # this is in MB
        output["ram"] = int(bucket["ramQuota"]) * 1024 * 1024
    else:
        logger.debug("No memory in bucket - setting to default")
        output["ram"] = 1024000
    if "compressionMode" in bucket:
        output["compressionMode"] = bucket["compressionMode"]
    else:
        output["compressionMode"] = None
    return output


def get_all_bucket_list_with_size(bucket_output):
    """
    Return bucket name with ramUsed( adjust ramused value )
    from bucket_output
    """

    additional_buffer = 10
    min_size = 104857600
    all_bucket_list = ""
    for line in bucket_output:
        if line.find(":") == -1:  # find the bucket name
            all_bucket_list = all_bucket_list + line + ","
        elif line.find("ramUsed") != -1:  # find ramUsed row in output
            ram_size = int(line.split(":")[1].strip())
            # Formula used used bucketsize/2 + 10% additional memory
            ram_size = (ram_size) / 2 + (
                (ram_size / 2) * additional_buffer // 100
            )
            if ram_size < min_size:
                ram_size = min_size
            all_bucket_list = all_bucket_list + str(ram_size) + ":"
    all_bucket_list = all_bucket_list.strip(":")
    logger.debug("All bucket list is: {}".format(all_bucket_list))
    return all_bucket_list.split(":")


def get_stg_all_bucket_list_with_ramquota_size(bucket_output):
    """Return bucket name with ramQuota from bucket_output. It will help in
    VDB creation as a reference value for
    bucket
    """
    logger.debug("bucket_output: {}".format(bucket_output))
    all_bucket_list = ""
    for line in bucket_output:
        if line.find(":") == -1:  # find the bucket name
            all_bucket_list = all_bucket_list + line + ","
        elif line.find("ramQuota") != -1:  # find ramQuota row in output
            ram_quota = int(line.split(":")[1].strip())
            all_bucket_list = all_bucket_list + str(ram_quota) + ":"
    all_bucket_list = all_bucket_list.strip(":")
    logger.debug("All bucket list is: {}".format(all_bucket_list))
    return all_bucket_list.split(":")


def filter_bucket_name_from_json(bucket_output):
    """Filter bucket name from bucket_output. Return list of
    bucket names present in  bucket_output"""
    output = [x["name"] for x in bucket_output if x["ram"] > 0]
    logger.debug("Bucket list: {}".format(output))
    return output


def filter_bucket_name_from_output(bucket_output):
    """
    Filter bucket name from bucket_output.
    Return list of bucket names present in  bucket_output
    """
    output = []
    logger.debug("filter input: {}".format(bucket_output))
    logger.debug("filter input: {}".format(len(bucket_output)))
    if bucket_output != []:
        output = list(map(lambda x: x["name"], bucket_output))
    logger.debug("Bucket list: {}".format(output))
    return output


def get_bucket_object(bucket_output, bucket):
    """
    Return bucket dict
    from bucket_output string for bucket(passed in argument)
    """
    output = filter(lambda x: x["name"] == bucket, bucket_output)
    if len(output) != 1:
        ret = None
    else:
        ret = output[-1]
    logger.debug("For Bucket {} detail is : {}".format(bucket, ret))
    return ret


def get_bucket_name_with_size(bucket_output, bucket):
    """
    Return `bucket_name:ramUsed`
    as output from bucket_output string for bucket(passed in argument)
    """

    logger.debug("HUHU")
    logger.debug(bucket_output)

    output = get_all_bucket_list_with_size(bucket_output)
    logger.debug("HAHA")
    logger.debug(output)
    output = ":".join(output)
    bucket_info = re.search(r"{},\d+".format(bucket), output).group()
    logger.debug("For Bucket {} detail is : {}".format(bucket, bucket_info))
    return bucket_info


def get_bucketlist_to_namesize_list(bucket_output, bucket_list):
    """Return `bucket_name:ramUsed` as output from bucket_output
    string for each bucket(passed in bucket_list)"""
    bucket_details = []
    for name in bucket_list:
        bucket_details.append(get_bucket_name_with_size(bucket_output, name))
    logger.debug(
        "Buckets: {}  \n details : {}".format(bucket_list, bucket_details)
    )
    return bucket_details


def sleepForSecond(sec):
    # Sleep/Pause the execution for given seconds
    logger.debug("sleeping for {}".format(sec))
    time.sleep(sec)
    logger.debug("sleeping is over")


def current_time():
    """Return current time in format of %Y%m%d%H%M%S'"""
    curr_time = datetime.now()
    return curr_time.strftime("%Y%m%d%H%M%S")


def get_value_of_key_from_json(json_obj, key):
    """return the value of key in provided json object"""
    value = json.loads(json_obj)[key]
    return value


def write_file(connection, content, filename):
    """Add given data into passed filename"""
    logger.debug("writing data {} in file {}".format(content, filename))
    try:
        utilities.execute_bash(
            connection,
            CommandFactory.write_file(data=content, filename=filename),
        )
    except Exception:
        logger.debug("Failed to Write into file")
        raise FileIOError("Failed to Write into file ")


def check_file_present(connection, config_file_path):
    """return True if file is present else return False"""
    try:
        stdout, stderr, exit_code = utilities.execute_bash(
            connection, CommandFactory.check_file(config_file_path)
        )
        if stdout == "Found":
            logger.debug("file path exist {}".format(config_file_path))
            return True
    except Exception:
        logger.debug("File path not exist {}".format(config_file_path))
    return False


def check_dir_present(connection, dir):
    """return True if directory is present else return False"""
    try:
        stdout, stderr, exit_code = utilities.execute_bash(
            connection, CommandFactory.check_directory(dir)
        )
        if stdout == "Found":
            logger.debug("dir path found {} ".format(dir))
            return True
    except Exception as err:
        logger.debug("directory path is absent: {}".format(str(err)))
    return False


def read_file(connection, filename):
    """read the file content and return the content"""
    logger.debug("Reading file {}".format(filename))
    command = CommandFactory.read_file(filename)
    stdout, stderr, exit_code = utilities.execute_bash(connection, command)
    return [stdout, stderr, exit_code]


# delete file
def delete_file(connection, filename):
    logger.debug("Deleting file {}".format(filename))
    stdout, stderr, exit_code = utilities.execute_bash(
        connection, CommandFactory.delete_file(filename)
    )
    return [stdout, stderr, exit_code]


# To generate the snapshot id each time using random function
def get_snapshot_id():
    return random.randint(100000000, 999999999)


def unmount_file_system(rx_connection, path):
    """unmount the file system which will use in cbbackup manager
    after post snapshot"""
    try:
        utilities.execute_bash(
            rx_connection, CommandFactory.unmount_file_system(path)
        )
    except Exception as err:
        logger.debug("error here {}".format(str(err)))
        raise UnmountFileSystemError(str(err))


def get_bucket_size_in_MB(bucket_size_list, bkt_name_size, bucket_name):
    """convert bkt size into MB if current bucket_size is zero"""
    bucket_size = 0
    for bucket_dict in bucket_size_list:
        bname = bucket_dict["bname"]
        bsize = bucket_dict["bsize"]
        if bname == "*" or bname == bucket_name:
            bucket_size = bsize
            break

    if bucket_size > 0:
        bkt_size_mb = bucket_size
    else:
        bkt_size_mb = int(bkt_name_size) // 1024 // 1024
    logger.debug("bkt_size_mb : {}".format(bkt_size_mb))
    return bkt_size_mb


def get_sync_lock_file_name(dsource_type, dsource_name):
    sync_filename = db_commands.constants.LOCK_SYNC_OPERATION
    if dsource_type == "XDCR":
        striped_dsource_name = dsource_name.replace(" ", "")
        sync_filename = str(striped_dsource_name) + str(sync_filename)
    return sync_filename


def check_stale_mountpoint(connection, path):

    output, stderr, exit_code = utilities.execute_bash(
        connection, CommandFactory.df(path)
    )
    if exit_code != 0:
        if "No such file or directory" in stderr:
            # this is actually OK
            return False
        else:
            logger.error("df retured error - stale mount point or other error")
            logger.error(
                "stdout: {} stderr: {} exit_code: {}".format(
                    output, stderr, exit_code
                )
            )
            return True
    else:
        return False


def check_server_is_used(connection, path):

    ret = Status.INACTIVE

    output, stderr, exit_code = utilities.execute_bash(
        connection, CommandFactory.mount()
    )
    if exit_code != 0:
        logger.error("mount retured error")
        logger.error(
            "stdout: {} stderr: {} exit_code: {}".format(
                output, stderr, exit_code
            )
        )
        raise UserError(
            "Problem with reading mounted file systems",
            "Ask OS admin to check mount",
            stderr,
        )
    else:
        # parse a mount output to find another Delphix mount points
        fs_re = re.compile(r"(\S*)\son\s(\S*)\stype\s(\S*)")
        for i in output.split("\n"):
            match = re.search(fs_re, i)
            if match is not None:
                groups = match.groups()
                if groups[2] and str(groups[2]).startswith("nfs"):
                    if path == groups[1]:
                        # this is our mount point - skip it
                        ret = Status.ACTIVE
                        continue
                    if "domain0" in groups[0] and "timeflow" in groups[0]:
                        # this is a delphix mount point but it's not ours
                        # raise an exception
                        raise UserError(
                            "Another database (VDB or staging) is using "
                            "this server.",
                            "Disable another one to provision or "
                            "enable this one",
                            "{} {}".format(groups[0], groups[1]),
                        )

    return ret


def clean_stale_mountpoint(connection, path):
    umount_std, umount_stderr, umount_exit_code = utilities.execute_bash(
        connection,
        CommandFactory.unmount_file_system(mount_path=path, options="-lf"),
    )
    if umount_exit_code != 0:
        logger.error("Problem with cleaning mount path")
        logger.error("stderr {}".format(umount_stderr))
        raise UserError(
            "Problem with cleaning mount path",
            "Ask OS admin to check mount points",
            umount_stderr,
        )
