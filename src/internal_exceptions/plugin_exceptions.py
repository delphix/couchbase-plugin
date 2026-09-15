#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
"""
Adding exceptions related to plugin
"""
##############################################################################

import logging

from internal_exceptions.base_exceptions import PluginException

logger = logging.getLogger(__name__)


class RepositoryDiscoveryError(PluginException):
    def __init__(self, message=""):
        message = "Not able to search repository information, " + message
        super(RepositoryDiscoveryError, self).__init__(
            message,
            "Check the COUCHBASE_PATH & couchbase installation",
            "Failed to search repository information",
        )


# This exception will be raised when failed to find source config
class SourceConfigDiscoveryError(PluginException):
    def __init__(self, message=""):
        message = "Failed to find source config, " + message
        super(SourceConfigDiscoveryError, self).__init__(
            message,
            "Stop the couchbase service if it is running",
            "Not able to find source",
        )


class MultipleSyncError(PluginException):
    def __init__(self, message=""):
        message = (
            "Resynchronization is in progress for other dSource, " + message
        )
        super(MultipleSyncError, self).__init__(
            message,
            "Please wait while the other resync operation completes and try "
            "again ",
            "Staging host already in use. Only Serial operations supported "
            "for couchbase",
        )


class MultipleXDCRSyncError(PluginException):
    def __init__(self, message=""):
        message = "XDCR setup found on staging host " + message
        super(MultipleXDCRSyncError, self).__init__(
            message,
            "Please use different staging host",
            "Multiple XDCR is not supported on single staging host",
        )


class MultipleSnapSyncError(PluginException):
    def __init__(self, message="", filename=""):
        logger.debug(
            "Exception MultipleSnapSyncError file: {}".format(filename)
        )
        message = "SnapSync is running for any other dSource " + message
        super(MultipleSnapSyncError, self).__init__(
            message,
            "Please wait while the other operation completes and try again "
            "or delete a lock file {}".format(filename),
            "Staging host already in use for SNAP-SYNC. Only Serial "
            "operations supported for couchbase",
        )


class FileIOError(PluginException):
    def __init__(self, message=""):
        message = "Failed to read/write operation from a file " + message
        super(FileIOError, self).__init__(
            message,
            "Verify the permission",
            "Please check the logs for more details",
        )


class MountPathError(PluginException):
    def __init__(self, message=""):
        message = (
            "Failed to create mount path because another file system is "
            "already mounted " + message
        )
        super(MountPathError, self).__init__(
            message,
            "Please re-try after the previous operation is completed",
            "Please check the logs for more details",
        )


class UnmountFileSystemError(PluginException):
    def __init__(self, message=""):
        message = (
            "Failed to unmount the file system from host in resync operation "
            + message
        )
        super(UnmountFileSystemError, self).__init__(
            message,
            "Please try again",
            "Please check the logs for more details",
        )


class MountPathStaleError(PluginException):
    def __init__(self, message=""):
        message = "Failed to get the stale mount path information " + message
        super(MountPathStaleError, self).__init__(
            message,
            "Please clean the stale mount point.",
            "Please check the logs for more details",
        )


ERR_RESPONSE_DATA = {
    "ERR_INSUFFICIENT_RAMQUOTA": {
        "MESSAGE": "Provided bucket size is not suffice to proceed",
        "ACTION": "Please change the bucket size and try again",
        "ERR_STRING": "RAM quota cannot be less than 100 MB",
    },
    "ERR_CBBKP_MGR1": {
        "MESSAGE": "Internal server error",
        "ACTION": "Please try again to run the previous operation",
        "ERR_STRING": "Internal server error while executing",
    },
    "ERR_RESTORE_CLUSTER": {
        "MESSAGE": "Internal server error",
        "ACTION": "Please try again to run the previous operation",
        "ERR_STRING": "Error restoring cluster",
    },
    "ERR_BUCKET_LIST_EMPTY": {
        "MESSAGE": "Please check configurations and try again",
        "ACTION": "Bucket list is empty. Please verify if the bucket exist "
        "at source",
        "ERR_STRING": "bucket list empty",
    },
    "ERR_UNABLE_TO_CONNECT": {
        "MESSAGE": "Internal server error, unable to connect",
        "ACTION": "Please verify the defined configurations and try again",
        "ERR_STRING": "Unable to connect to host",
    },
    "ERR_UNRECOGNIZED_ARGS": {
        "MESSAGE": "Argument(s) mismatch. Please check logs for more details",
        "ACTION": "Please provide correct configuration details and try again",
        "ERR_STRING": "unrecognized arguments",
    },
    "ERR_INCORRECT_CREDENTIAL": {
        "MESSAGE": "Invalid credentials",
        "ACTION": "Try again with correct credentials",
        "ERR_STRING": "please check your username",
    },
    "ERR_REPLICATION_ALREADY_PRESENT": {
        "MESSAGE": "Duplicate cluster name found",
        "ACTION": "Delete existing staging cluster configuration on source "
        "or use different staging cluster name",
        "ERR_STRING": "Replication to the same remote cluster and bucket "
        "already exists",
    },
    "ERR_DUPLICATE_CLUSTER_NAME": {
        "MESSAGE": "Duplicate cluster name found",
        "ACTION": "Delete existing staging cluster configuration on source "
        "or use different staging cluster name ",
        "ERR_STRING": "Duplicate cluster names are not allowed",
    },
    "ERR_INTERNAL_SERVER_ERROR": {
        "MESSAGE": "Internal server error, unable to connect",
        "ACTION": "Please verify the defined configurations and try again",
        "ERR_STRING": "Internal server error, please retry your request",
    },
    "ERR_INTERNAL_SERVER_ERROR1": {
        "MESSAGE": "Internal server error, unable to connect",
        "ACTION": "Please verify the defined configurations and try again",
        "ERR_STRING": "Unable to connect to host",
    },
    "ERR_XDCR_OPERATION_ERROR": {
        "MESSAGE": "Unable to set up XDCR",
        "ACTION": "Please correct parameters and try again",
        "ERR_STRING": "Replication Error",
    },
    "ERR_CB_BACKUP_MANGER_FAILED": {
        "MESSAGE": "Unable to restore backup",
        "ACTION": "Please verify the provided archive path and try again",
        "ERR_STRING": "Error restoring cluster: Bucket Backup",
    },
    "ERR_SERVICE_UNAVAILABLE_ERROR": {
        "MESSAGE": "Unable to restore backup",
        "ACTION": "Please try again ",
        "ERR_STRING": "is not available on target",
    },
    "ERR_UNEXPECTED_ERROR1": {
        "MESSAGE": "Unable to restore backup",
        "ACTION": "Please try again ",
        "ERR_STRING": "Running this command will totally PURGE database "
        "data from disk. Do you really want to do",
    },
    "ERR_INVALID_BACKUP_DIR": {
        "MESSAGE": "Unable to restore backup",
        "ACTION": "Try again with correct archive location. ",
        "ERR_STRING": "Archive directory .* doesn't exist",
    },
    "DEFAULT_ERR": {
        "MESSAGE": "Internal error occurred, retry again",
        "ACTION": "Please check logs for more details",
        "ERR_STRING": "Default error string",
    },
}
