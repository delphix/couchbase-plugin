#
# Copyright (c) 2020-2024 by Delphix. All rights reserved.
#
#

import logging
import os

from controller.couchbase_operation import CouchbaseOperation
from controller.helper_lib import check_server_is_used
from controller.helper_lib import check_stale_mountpoint
from controller.helper_lib import clean_stale_mountpoint
from controller.resource_builder import Resource
from dlpx.virtualization.common import RemoteConnection
from dlpx.virtualization.common import RemoteEnvironment
from dlpx.virtualization.common import RemoteHost
from dlpx.virtualization.common import RemoteUser
from dlpx.virtualization.platform import Mount
from dlpx.virtualization.platform import MountSpecification
from dlpx.virtualization.platform import OwnershipSpecification
from dlpx.virtualization.platform import Plugin
from operations import discovery
from operations import linked
from operations import virtual
from utils import setup_logger

plugin = Plugin()
setup_logger._setup_logger()

logger = logging.getLogger(__name__)


@plugin.upgrade.linked_source("2023.10.27.01")
def update_bucket_size(old_linked_source):
    logger.debug(f"Started upgrade update_bucket_size:{old_linked_source}")
    old_linked_source = dict(old_linked_source)
    if isinstance(old_linked_source["bucketSize"], int):
        if old_linked_source["bucketSize"] == 0:
            old_linked_source["bucketSize"] = []
        else:
            d = [{"bname": "*", "bsize": old_linked_source["bucketSize"]}]
            old_linked_source["bucketSize"] = d
    logger.debug(f"Completed update_bucket_size: {old_linked_source}")
    return old_linked_source


@plugin.upgrade.linked_source("2023.10.27.02")
def update_archive_name(old_linked_source):
    logger.debug(f"Started upgrade update_archive_name:{old_linked_source}")
    old_linked_source = dict(old_linked_source)
    if "archiveName" not in old_linked_source.keys():
        if old_linked_source["couchbaseBakLoc"] == "":
            old_linked_source["archiveName"] = ""
        else:
            old_linked_source["archiveName"] = os.path.basename(
                old_linked_source["couchbaseBakLoc"]
            )
            old_linked_source["couchbaseBakLoc"] = os.path.dirname(
                old_linked_source["couchbaseBakLoc"]
            )
    logger.debug(f"Completed update_archive_name: {old_linked_source}")
    return old_linked_source


#
# Below is an example of the repository discovery operation.
#
# NOTE: The decorators are defined on the 'plugin' object created above.
#
# Mark the function below as the operation that does repository discovery.
@plugin.discovery.repository()
def repository_discovery(source_connection):
    #
    # This is an object generated from the repositoryDefinition schema.
    # In order to use it locally you must run the 'build -g' command provided
    # by the SDK tools from the plugin's root directory.
    #
    return discovery.find_repos(source_connection)


@plugin.discovery.source_config()
def source_config_discovery(source_connection, repository):
    #
    # To have automatic discovery of source configs, return a list of
    # SourceConfigDefinitions similar to the list of
    # RepositoryDefinitions above.
    #
    return discovery.find_source(source_connection, repository)


@plugin.linked.post_snapshot()
def linked_post_snapshot(
    staged_source, repository, source_config, optional_snapshot_parameters
):
    return linked.post_snapshot(
        staged_source,
        repository,
        source_config,
        staged_source.parameters.d_source_type,
    )


@plugin.linked.mount_specification()
def linked_mount_specification(staged_source, repository):
    mount_path = staged_source.parameters.mount_path

    if check_stale_mountpoint(staged_source.staged_connection, mount_path):
        cleanup_process = CouchbaseOperation(
            Resource.ObjectBuilder.set_staged_source(staged_source)
            .set_repository(repository)
            .build()
        )
        cleanup_process.stop_couchbase()
        clean_stale_mountpoint(staged_source.staged_connection, mount_path)

    check_server_is_used(staged_source.staged_connection, mount_path)

    environment = staged_source.staged_connection.environment
    linked.check_mount_path(staged_source, repository)
    logger.debug("Mounting path {}".format(mount_path))
    mounts = [Mount(environment, mount_path)]
    logger.debug(
        "Setting ownership to uid {} and gid {}".format(
            repository.uid,
            repository.gid,
        )
    )
    ownership_spec = OwnershipSpecification(repository.uid, repository.gid)
    return MountSpecification(mounts, ownership_spec)


@plugin.linked.pre_snapshot()
def linked_pre_snapshot(
    staged_source, repository, source_config, optional_snapshot_parameters
):
    if optional_snapshot_parameters and optional_snapshot_parameters.resync:
        linked.resync(
            staged_source, repository, source_config, staged_source.parameters
        )
    else:
        linked.pre_snapshot(
            staged_source, repository, source_config, staged_source.parameters
        )


@plugin.linked.status()
def linked_status(staged_source, repository, source_config):
    return linked.d_source_status(staged_source, repository, source_config)


@plugin.linked.stop_staging()
def stop_staging(staged_source, repository, source_config):
    linked.stop_staging(staged_source, repository, source_config)


@plugin.linked.start_staging()
def start_staging(staged_source, repository, source_config):
    linked.start_staging(staged_source, repository, source_config)


@plugin.virtual.configure()
def configure(virtual_source, snapshot, repository):
    return virtual.vdb_configure(virtual_source, snapshot, repository)


@plugin.virtual.reconfigure()
def reconfigure(virtual_source, repository, source_config, snapshot):
    return virtual.vdb_reconfigure(
        virtual_source,
        repository,
        source_config,
        snapshot,
    )


@plugin.virtual.pre_snapshot()
def virtual_pre_snapshot(virtual_source, repository, source_config):
    virtual.vdb_pre_snapshot(virtual_source, repository, source_config)


@plugin.virtual.post_snapshot()
def virtual_post_snapshot(virtual_source, repository, source_config):
    return virtual.post_snapshot(virtual_source, repository, source_config)


@plugin.virtual.start()
def start(virtual_source, repository, source_config):
    virtual.vdb_start(virtual_source, repository, source_config)


@plugin.virtual.stop()
def stop(virtual_source, repository, source_config):
    virtual.vdb_stop(virtual_source, repository, source_config)


@plugin.virtual.mount_specification()
def virtual_mount_specification(virtual_source, repository):
    mount_path = virtual_source.parameters.mount_path

    if check_stale_mountpoint(virtual_source.connection, mount_path):
        cleanup_process = CouchbaseOperation(
            Resource.ObjectBuilder.set_virtual_source(virtual_source)
            .set_repository(repository)
            .build()
        )
        cleanup_process.stop_couchbase()
        clean_stale_mountpoint(virtual_source.connection, mount_path)

    check_server_is_used(virtual_source.connection, mount_path)

    mounts = [Mount(virtual_source.connection.environment, mount_path)]
    logger.debug("Mounting path {}".format(mount_path))
    logger.debug(
        "Setting ownership to uid {} and gid {}".format(
            repository.uid,
            repository.gid,
        )
    )
    ownership_spec = OwnershipSpecification(repository.uid, repository.gid)

    logger.debug(
        "in mounting: {}".format(
            str(virtual_source.parameters.node_list),
        )
    )

    if (
        virtual_source.parameters.node_list is not None
        and len(virtual_source.parameters.node_list) > 0
    ):
        # more nodes
        for m in virtual_source.parameters.node_list:
            logger.debug("in loop: {}".format(str(m)))
            node_host = RemoteHost(
                name="foo",
                reference=m["environment"].replace("_ENVIRONMENT", ""),
                binary_path="",
                scratch_path="",
            )
            e = RemoteEnvironment("foo", m["environment"], node_host)
            mount = Mount(e, mount_path)
            mounts.append(mount)

            user = RemoteUser(name="unused", reference=m["environmentUser"])
            environment = RemoteEnvironment(
                name="unused", reference=m["environment"], host=node_host
            )
            clean_node_conn = RemoteConnection(
                environment=environment,
                user=user,
            )

            if check_stale_mountpoint(clean_node_conn, mount_path):
                clean_node = CouchbaseOperation(
                    Resource.ObjectBuilder.set_virtual_source(virtual_source)
                    .set_repository(repository)
                    .build(),
                    clean_node_conn,
                )
                clean_node.stop_couchbase()
                clean_stale_mountpoint(clean_node_conn, mount_path)

            check_server_is_used(clean_node_conn, mount_path)

    return MountSpecification(mounts, ownership_spec)


@plugin.virtual.status()
def virtual_status(virtual_source, repository, source_config):
    logger.debug("in status")
    return virtual.vdb_status(virtual_source, repository, source_config)


@plugin.virtual.unconfigure()
def unconfigure(virtual_source, repository, source_config):
    logger.debug("UNCONFIGURE")
    virtual.vdb_unconfigure(virtual_source, repository, source_config)


@plugin.upgrade.virtual_source("2021.07.19")
def add_node_to_virtual(old_virtual_source):
    new_virt = dict(old_virtual_source)
    new_virt["node_list"] = []
    return new_virt


@plugin.upgrade.virtual_source("2021.10.06")
def add_node_to_virtual1(old_virtual_source):
    logger.debug("Doing upgrade to node_addr")
    new_virt = dict(old_virtual_source)
    logger.debug(new_virt)
    for i in new_virt["node_list"]:
        i["node_addr"] = ""
    logger.debug("After changes")
    logger.debug(new_virt)
    return new_virt


@plugin.linked.source_size()
def linked_source_size(staged_source, repository, source_config):
    return linked.source_size(staged_source, repository, source_config)
