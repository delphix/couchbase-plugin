#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#
##############################################################################
# In this module, functions defined for XDCR ingestion mechanism.
##############################################################################

import json
import logging

import db_commands
from controller import helper_lib
from controller.couchbase_operation import CouchbaseOperation
from controller.resource_builder import Resource
from dlpx.virtualization.platform.exceptions import UserError
from generated.definitions import SnapshotDefinition
from internal_exceptions.plugin_exceptions import MultipleSyncError
from operations import config
from operations import linking

logger = logging.getLogger(__name__)


def resync_xdcr(staged_source, repository, source_config, input_parameters):
    logger.debug("START resync_xdcr")
    if input_parameters.xdcr_admin_password == "":
        raise UserError("Source password is mandatory in XDCR dsource type!")
    dsource_type = input_parameters.d_source_type
    dsource_name = source_config.pretty_name
    resync_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source)
        .set_repository(repository)
        .set_source_config(source_config)
        .build()
    )

    couchbase_host = input_parameters.couchbase_host

    linking.check_for_concurrent(
        resync_process, dsource_type, dsource_name, couchbase_host
    )

    linking.configure_cluster(resync_process)

    # common steps for both XDCR & CB back up

    bucket_details_source = resync_process.source_bucket_list()
    bucket_details_staged = resync_process.bucket_list()
    buckets_toprocess = linking.buckets_precreation(
        resync_process, bucket_details_source, bucket_details_staged
    )

    # run this for all buckets
    resync_process.setup_replication()

    logger.debug("Finding staging_uuid & cluster_name on staging")
    staging_uuid = resync_process.get_replication_uuid()

    if staging_uuid is None:
        logger.debug("Can't find a replication UUID after setting it up")
        raise UserError("Can't find a replication UUID after setting it up")

    for bkt in buckets_toprocess:
        resync_process.monitor_bucket(bkt, staging_uuid)

    linking.build_indexes(resync_process)

    logger.info("Stopping Couchbase")
    resync_process.stop_couchbase()
    resync_process.save_config("parent")


def pre_snapshot_xdcr(
    staged_source, repository, source_config, input_parameters
):
    logger.info("In Pre snapshot...")
    pre_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source)
        .set_repository(repository)
        .set_source_config(source_config)
        .build()
    )
    config.SNAP_SYNC_FILE_NAME = (
        pre_snapshot_process.create_config_dir()
        + "/"
        + db_commands.constants.LOCK_SNAPSYNC_OPERATION
    )
    # Don't care of sync.lck file as it will never de deleted even in post
    # snapshot.
    if helper_lib.check_file_present(
        staged_source.staged_connection, config.SNAP_SYNC_FILE_NAME
    ):
        config.SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = (
            False
        )
        raise MultipleSyncError()
    else:
        logger.debug("Creating lock file...")
        msg = db_commands.constants.RESYNCE_OR_SNAPSYNC_FOR_OTHER_OBJECT_IN_PROGRESS.format(  # noqa E501
            source_config.pretty_name, input_parameters.couchbase_host
        )
        helper_lib.write_file(
            staged_source.staged_connection, msg, config.SNAP_SYNC_FILE_NAME
        )
    logger.info("Stopping Couchbase")
    pre_snapshot_process.stop_couchbase()
    pre_snapshot_process.save_config("parent")


def post_snapshot_xdcr(staged_source, repository, source_config, dsource_type):
    logger.info("In Post snapshot...")
    post_snapshot_process = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source)
        .set_repository(repository)
        .set_source_config(source_config)
        .build()
    )

    # post_snapshot_process.save_config()
    post_snapshot_process.start_couchbase()
    snapshot = SnapshotDefinition(validate=False)

    ind = post_snapshot_process.get_indexes_definition()
    logger.debug("indexes definition : {}".format(ind))

    snapshot.indexes = ind

    bucket_details = post_snapshot_process.bucket_list()

    snapshot.db_path = staged_source.parameters.mount_path
    snapshot.couchbase_port = source_config.couchbase_src_port
    snapshot.couchbase_host = source_config.couchbase_src_host
    snapshot.bucket_list = json.dumps(bucket_details)
    snapshot.time_stamp = helper_lib.current_time()
    snapshot.snapshot_id = str(helper_lib.get_snapshot_id())
    snapshot.couchbase_admin = post_snapshot_process.parameters.couchbase_admin
    snapshot.couchbase_admin_password = (
        post_snapshot_process.parameters.couchbase_admin_password
    )
    # logger.debug("snapshot schema: {}".format(snapshot))
    logger.debug(
        "Deleting the snap sync lock file {}".format(
            config.SNAP_SYNC_FILE_NAME
        )
    )
    helper_lib.delete_file(
        staged_source.staged_connection, config.SNAP_SYNC_FILE_NAME
    )
    return snapshot


def start_staging_xdcr(staged_source, repository, source_config):
    start_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source)
        .set_repository(repository)
        .set_source_config(source_config)
        .build()
    )

    logger.debug("Enabling the D_SOURCE:{}".format(source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    rx_connection = staged_source.staged_connection

    start_staging.stop_couchbase()
    start_staging.delete_config()
    # TODO error handling
    start_staging.restore_config(what="current")
    start_staging.start_couchbase()

    start_staging.setup_replication()

    config_dir = start_staging.create_config_dir()
    msg = "dSource Creation / Snapsync for dSource {} is in progress".format(
        source_config.pretty_name
    )
    helper_lib.write_file(
        rx_connection,
        msg,
        config_dir
        + "/"
        + helper_lib.get_sync_lock_file_name(
            dsource_type, source_config.pretty_name
        ),
    )
    logger.debug("D_SOURCE:{} enabled".format(source_config.pretty_name))


def stop_staging_xdcr(staged_source, repository, source_config):
    stop_staging = CouchbaseOperation(
        Resource.ObjectBuilder.set_staged_source(staged_source)
        .set_repository(repository)
        .set_source_config(source_config)
        .build()
    )

    logger.debug("Disabling the D_SOURCE:{}".format(source_config.pretty_name))
    dsource_type = staged_source.parameters.d_source_type
    rx_connection = staged_source.staged_connection
    logger.info("Deleting Existing Replication")
    is_xdcr_setup, cluster_name = stop_staging.delete_replication()
    if is_xdcr_setup:
        logger.info("Deleting XDCR")
        stop_staging.xdcr_delete(cluster_name)
    config_dir = stop_staging.create_config_dir()
    helper_lib.delete_file(
        rx_connection,
        config_dir
        + "/"
        + helper_lib.get_sync_lock_file_name(
            dsource_type, source_config.pretty_name
        ),
    )
    stop_staging.stop_couchbase()
    stop_staging.save_config(what="current")
    stop_staging.delete_config()
    logger.debug("D_SOURCE:{} disabled".format(source_config.pretty_name))
