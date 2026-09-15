#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#
##############################################################################
# In this module, functions defined common ingestion modes - backup and xdcr
##############################################################################

import logging
import os
import time

import db_commands
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
from controller.resource_builder import Resource
from dlpx.virtualization.platform import Status
from dlpx.virtualization.platform.exceptions import UserError
from internal_exceptions.plugin_exceptions import MultipleXDCRSyncError
from operations import config

logger = logging.getLogger(__name__)


# potentially to remove - as checks are done on the mount points
def check_for_concurrent(
    couchbase_obj,
    dsource_type,
    dsource_name,
    couchbase_host,
):
    config_dir = couchbase_obj.create_config_dir()

    config.SYNC_FILE_NAME = (
        config_dir
        + "/"
        + helper_lib.get_sync_lock_file_name(dsource_type, dsource_name)
    )

    delphix_config_dir = couchbase_obj.get_config_directory()
    logger.debug("Check if we have config dir in Delphix storage")
    if not helper_lib.check_dir_present(
        couchbase_obj.connection,
        delphix_config_dir,
    ):
        logger.debug("make Delphix storage dir:{}".format(delphix_config_dir))
        couchbase_obj.make_directory(delphix_config_dir)

    if not verify_sync_lock_file_for_this_job(
        couchbase_obj.connection, config.SYNC_FILE_NAME
    ):
        config.SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = False
        logger.debug("Sync file is already created by other dSource")
        raise MultipleXDCRSyncError(
            "Sync file is already created by other dSource",
        )
    else:
        # creating sync  file
        msg = db_commands.constants.RESYNCE_OR_SNAPSYNC_FOR_OTHER_OBJECT_IN_PROGRESS.format(  # noqa E501
            dsource_name, couchbase_host
        )
        helper_lib.write_file(
            couchbase_obj.connection,
            msg,
            config.SYNC_FILE_NAME,
        )


def verify_sync_lock_file_for_this_job(rx_connection, sync_filename):
    if helper_lib.check_file_present(rx_connection, sync_filename):
        logger.debug("Sync File Present: {}".format(sync_filename))
        return True
    config_dir = os.path.dirname(sync_filename)

    possible_sync_filename = "/*" + db_commands.constants.LOCK_SYNC_OPERATION
    possible_sync_filename = config_dir + possible_sync_filename
    logger.debug("Checking for {}".format(possible_sync_filename))
    if helper_lib.check_file_present(rx_connection, possible_sync_filename):
        return False
    return True


def configure_cluster(couchbase_obj):
    # configure Couchbase cluster

    logger.debug("Checking cluster config")
    if couchbase_obj.check_config():
        logger.debug("cluster config found - restoring")
        couchbase_obj.stop_couchbase()
        couchbase_obj.restore_config()
        couchbase_obj.start_couchbase()
    else:
        logger.debug("cluster config not found - preparing node")
        # no config in delphix directory
        # initial cluster setup
        couchbase_obj.delete_xdcr_config()
        couchbase_obj.stop_couchbase()
        couchbase_obj.delete_data_folder()
        couchbase_obj.delete_config_folder()

        # we can't use normal monitor as server is not configured yet
        couchbase_obj.start_couchbase(no_wait=True)

        end_time = time.time() + 3660

        server_status = Status.INACTIVE

        # break the loop either end_time is exceeding from 1 hour or
        # server is successfully started
        while time.time() < end_time and server_status != Status.ACTIVE:
            helper_lib.sleepForSecond(1)  # waiting for 1 second
            # fetching status
            server_status = couchbase_obj.staging_bootstrap_status()
            logger.debug("server status {}".format(server_status))

        # check if cluster not configured and raise an issue
        if couchbase_obj.check_cluster_notconfigured():
            logger.debug("Node not configured - creating a new cluster")
            couchbase_obj.node_init()
            couchbase_obj.cluster_init()
            logger.debug("Cluster configured")
        else:
            logger.debug("Node configured but no configuration in Delphix")
            if couchbase_obj.check_cluster_configured():
                logger.debug(
                    "Configured with staging user/password and alive "
                    "so not a problem - continue"
                )
            else:
                logger.debug(
                    "Cluster configured but not with user/password given "
                    "in Delphix potentially another cluster"
                )
                raise UserError(
                    "Cluster configured but not with user/password given "
                    "in Delphix potentially another cluster"
                )


def buckets_precreation(
    couchbase_obj,
    bucket_details_source,
    bucket_details_staged,
):
    # common steps for both XDCR & CB back up
    # return a list of precreated buckets to process
    logger.debug("buckets_precreation")
    bucket_list = []
    config_setting = couchbase_obj.parameters.config_settings_prov
    log_msg = "Bucket names passed for configuration: {}".format(
        config_setting,
    )
    logger.debug(log_msg)
    bucket_configured_staged = []
    if len(config_setting) > 0:
        # process for list of buckets
        logger.debug("Getting bucket information from config")
        buckets_dict = {b["name"]: b for b in bucket_details_source}
        for config_bucket in config_setting:
            bucket_configured_staged.append(config_bucket["bucketName"])
            log_msg = "Filtering bucket name with size only from above output"
            logger.debug(log_msg)
            bucket = buckets_dict[config_bucket["bucketName"]]
            logger.debug("Running bucket operations for {}".format(bucket))
            bkt_name = config_bucket["bucketName"]
            bkt_size = bucket["ram"]
            bkt_type = bucket["bucketType"]
            bkt_compression = bucket["compressionMode"]

            bkt_size_mb = helper_lib.get_bucket_size_in_MB(
                couchbase_obj.parameters.bucket_size, bkt_size, bkt_name
            )

            if config_bucket["bucketName"] not in bucket_details_staged:
                couchbase_obj.bucket_create(
                    config_bucket["bucketName"],
                    bkt_size_mb,
                    bkt_type,
                    bkt_compression,
                )
            else:
                logger.debug(
                    "Bucket {} already present in staged environment. "
                    "Recreating bucket ".format(config_bucket["bucketName"])
                )
                couchbase_obj.bucket_remove(config_bucket["bucketName"])
                couchbase_obj.bucket_create(
                    config_bucket["bucketName"],
                    bkt_size_mb,
                    bkt_type,
                    bkt_compression,
                )

            bucket_list.append(config_bucket["bucketName"])

        logger.debug("Finding buckets present at staged server")
        bucket_details_staged = couchbase_obj.bucket_list()
        filter_bucket_list = helper_lib.filter_bucket_name_from_output(
            bucket_details_staged
        )
        extra_bucket = set(filter_bucket_list) - set(bucket_configured_staged)
        extra_bucket = list(extra_bucket)

        logger.debug("Extra bucket found to delete:{} ".format(extra_bucket))
        for bucket in extra_bucket:
            couchbase_obj.bucket_remove(bucket)
    else:
        # process for all buckets
        # filter_source_bucket = helper_lib.filter_bucket_name_from_json(
        #     bucket_details_source
        # )
        for items in bucket_details_source:
            if items:
                logger.debug("Running bucket operations for {}".format(items))
                bkt_name = items["name"]
                bkt_size = items["ram"]
                bkt_type = items["bucketType"]
                bkt_compression = items["compressionMode"]

                bkt_size_mb = helper_lib.get_bucket_size_in_MB(
                    couchbase_obj.parameters.bucket_size, bkt_size, bkt_name
                )
                if bkt_name not in bucket_details_staged:
                    couchbase_obj.bucket_create(
                        bkt_name, bkt_size_mb, bkt_type, bkt_compression
                    )
                else:
                    logger.debug(
                        "Bucket {} already present in staged environment. "
                        "Recreating bucket ".format(bkt_name)
                    )
                    couchbase_obj.bucket_remove(bkt_name)
                    couchbase_obj.bucket_create(
                        bkt_name, bkt_size_mb, bkt_type, bkt_compression
                    )
                bucket_list.append(bkt_name)

    return bucket_list


def build_indexes(couchbase_obj):
    # create indexes based on the index definition

    logger.debug("index builder")
    ind = couchbase_obj.get_indexes_definition()
    logger.debug("indexes definition : {}".format(ind))
    for i in ind:
        logger.debug(i)
        couchbase_obj.build_index(i)
    couchbase_obj.check_index_build()


def d_source_status(staged_source, repository, source_config):
    status_obj = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source)
        .set_repository(repository)
        .set_source_config(source_config)
        .build()
    )
    logger.debug(
        "Checking status for D_SOURCE: {}".format(
            source_config.pretty_name,
        )
    )
    return status_obj.status()
