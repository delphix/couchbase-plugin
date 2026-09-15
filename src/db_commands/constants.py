#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
# This module is created to define constants values which are being used in
# this plugin.
##############################################################################

# Constants
LOCK_SYNC_OPERATION = "DO_NOT_DELETE_DELPHIX_sync.lck"
LOCK_SNAPSYNC_OPERATION = "DO_NOT_DELETE_DELPHIX_snapsync.lck"
SRC_BUCKET_INFO_FILENAME = "couchbase_src_bucket_info.cfg"
ENV_VAR_KEY = "environment_vars"
StatusIsActive = "healthy"  # it shows the status of server is good
# Folder inside which config file will create
DELPHIX_HIDDEN_FOLDER = ".delphix"
CONFIG_FILE_NAME = "config.txt"
EVICTION_POLICY = "valueOnly"
DEFAULT_CB_BIN_PATH = "/opt/couchbase/bin"
CBBKPMGR = "Couchbase Backup Manager"
XDCR = "XDCR"


# String literals to match and throw particular type of exceptions.
# used by db_exception_handler.py
ALREADY_CLUSTER_INIT = (
    "Cluster is already initialized, use setting-cluster to change settings"
)
SHUTDOWN_FAILED = "shutdown failed"
BUCKET_NAME_ALREADY_EXIST = "Bucket with given name already exists"
MULTIPLE_VDB_ERROR = (
    "Changing data of nodes that are part of provisioned "
    "cluster is not supported"
)
CLUSTER_ALREADY_PRESENT = (
    "Cluster reference to the same cluster already exists under the name"
)
ALREADY_CLUSTER_FOR_BUCKET = (
    "Replication to the same remote cluster and bucket already exists"
)

# used by linked.py
ALREADY_SYNC_FILE_PRESENT_ON_HOST = (
    "Not cleaning lock files as not created by this job. "
    "Also check, is there any XDCR set up on this host. If yes "
    "then sync file should not be deleted "
)
RESYNCE_OR_SNAPSYNC_FOR_OTHER_OBJECT_IN_PROGRESS = (
    "dSource Creation / Snapsync for dSource {} is in progress. "
    "Same staging server {} cannot be used for other operations"
)
