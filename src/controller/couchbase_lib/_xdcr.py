#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
"""
This class contains methods for XDCR related operations.
This is child class of Resource and parent class of CouchbaseOperation
"""
import json

##############################################################################
import logging
import re

from controller import helper_lib
from controller.couchbase_lib._mixin_interface import MixinInterface
from controller.resource_builder import Resource
from db_commands.commands import CommandFactory
from db_commands.constants import ENV_VAR_KEY
from dlpx.virtualization.platform.exceptions import UserError
from utils import utilities

logger = logging.getLogger(__name__)


class _XDCrMixin(Resource, MixinInterface):
    def __init__(self, builder):
        super(_XDCrMixin, self).__init__(builder)

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {
            "shell_path": self.repository.cb_shell_path,
            "source_hostname": self.source_config.couchbase_src_host,
            "source_port": self.source_config.couchbase_src_port,
            "source_username": self.parameters.xdcr_admin,
            "hostname": self.connection.environment.host.name,
            "port": self.parameters.couchbase_port,
            "username": self.parameters.couchbase_admin,
        }
        # MixinInterface.read_map(env)
        return env

    def xdcr_delete(self, cluster_name):
        logger.debug(
            "XDCR deletion for cluster_name {} has started ".format(
                cluster_name
            )
        )
        kwargs = {
            ENV_VAR_KEY: {
                "source_password": self.parameters.xdcr_admin_password,
                "password": self.parameters.couchbase_admin_password,
            }
        }
        env = _XDCrMixin.generate_environment_map(self)
        env.update(kwargs[ENV_VAR_KEY])
        cmd, env_vars = CommandFactory.xdcr_delete_expect(
            cluster_name=cluster_name, **env
        )
        kwargs[ENV_VAR_KEY].update(env_vars)
        stdout, stderr, exit_code = utilities.execute_expect(
            self.connection, cmd, **kwargs
        )
        if exit_code != 0:
            logger.error("XDCR Setup deletion failed")
            if stdout:
                if re.search(r"unable to access the REST API", stdout):
                    raise Exception(stdout)
                elif re.search(r"unknown remote cluster", stdout):
                    raise Exception(stdout)
        else:
            logger.debug("XDCR Setup deletion succeeded")

    def xdcr_setup(self):
        logger.debug("Started XDCR set up ...")
        kwargs = {
            ENV_VAR_KEY: {
                "source_password": self.parameters.xdcr_admin_password,
                "password": self.parameters.couchbase_admin_password,
            }
        }
        env = _XDCrMixin.generate_environment_map(self)
        env.update(kwargs[ENV_VAR_KEY])
        cmd, env_vars = CommandFactory.xdcr_setup_expect(
            cluster_name=self.parameters.stg_cluster_name, **env
        )
        kwargs[ENV_VAR_KEY].update(env_vars)
        utilities.execute_expect(self.connection, cmd, **kwargs)
        helper_lib.sleepForSecond(3)

    def xdcr_replicate(self, src, tgt):
        try:
            logger.debug("Started XDCR replication for bucket {}".format(src))
            kwargs = {
                ENV_VAR_KEY: {
                    "source_password": self.parameters.xdcr_admin_password
                }
            }
            env = _XDCrMixin.generate_environment_map(self)
            env.update(kwargs[ENV_VAR_KEY])
            cmd, env_vars = CommandFactory.xdcr_replicate_expect(
                source_bucket_name=src,
                target_bucket_name=tgt,
                cluster_name=self.parameters.stg_cluster_name,
                **env,
            )
            kwargs[ENV_VAR_KEY].update(env_vars)
            stdout, stderr, exit_code = utilities.execute_expect(
                self.connection, cmd, **kwargs
            )
            if exit_code != 0:
                logger.debug("XDCR replication create failed")
                raise Exception(stdout)
            logger.debug("{} : XDCR replication create succeeded".format(tgt))
            helper_lib.sleepForSecond(2)
        except Exception as e:
            logger.debug("XDCR error {}".format(str(e)))

    def get_replication_uuid(self):
        # False for string
        logger.debug("Finding the replication uuid through host name")
        cluster_name = self.parameters.stg_cluster_name

        stdout, stderr, exit_code = self.run_couchbase_command(
            "get_replication_uuid",
            source_hostname=self.source_config.couchbase_src_host,
            source_port=self.source_config.couchbase_src_port,
            source_username=self.parameters.xdcr_admin,
            source_password=self.parameters.xdcr_admin_password,
        )

        if exit_code != 0 or stdout is None or stdout == "":
            logger.debug("No Replication ID identified")
            return None

        try:

            logger.debug("xdcr remote references : {}".format(stdout))
            stg_hostname = self.connection.environment.host.name
            logger.debug("Environment hostname {}".format(stg_hostname))
            # it can have more than single IP address
            host_ips = self.get_ip()
            # conver output into variables
            clusters = {}
            l = stdout.split("\n")
            while l:
                line = l.pop(0)
                g = re.match(r"\s*cluster name:\s(\S*)", line)
                if g:
                    xdrc_cluster_name = g.group(1)
                    uuid = re.match(r"\s*uuid:\s(\S*)", l.pop(0)).group(1)
                    hostname = re.match(
                        r"\s*host name:\s(\S*):(\d*)", l.pop(0)
                    ).group(1)
                    clusters[xdrc_cluster_name.lower()] = {
                        "hostname": hostname,
                        "uuid": uuid,
                    }

            # check if a cluster name is really connected to staging -
            # just in case

            if cluster_name.lower() in clusters:
                logger.debug(
                    "Cluster {} found in xdrc-setup output".format(
                        cluster_name
                    )
                )
                # check if hostname returned from source match hostname or
                # IP's of staging server

                logger.debug(stg_hostname)
                logger.debug(clusters[cluster_name.lower()]["hostname"])

                if stg_hostname == clusters[cluster_name.lower()]["hostname"]:
                    # hostname matched
                    logger.debug(
                        "Cluster {} hostname {} is matching staging server "
                        "hostname".format(cluster_name, stg_hostname)
                    )
                    uuid = clusters[cluster_name.lower()]["uuid"]
                else:
                    # check for IP's
                    logger.debug("Checking for IP match")

                    logger.debug(clusters[cluster_name.lower()])

                    if clusters[cluster_name.lower()]["hostname"] in host_ips:
                        # ip matched
                        logger.debug(
                            "Cluster {} IP {} is matching staging server IPs "
                            "{}".format(
                                cluster_name,
                                clusters[cluster_name.lower()]["hostname"],
                                host_ips,
                            )
                        )
                        uuid = clusters[cluster_name.lower()]["uuid"]
                    else:
                        logger.debug(
                            "Can't confirm that xdrc-setup is matching staging"
                        )
                        raise UserError(
                            "XDRC Remote cluster {} on the source server "
                            "is not pointed to staging server".format(
                                cluster_name
                            ),
                            "Please check and delete remote cluster "
                            "definition",
                            clusters[cluster_name.lower()],
                        )

            else:
                logger.debug(
                    "Cluster {} configuration  not found in XDCR of "
                    "source".format(cluster_name)
                )
                return None

            logger.debug("uuid for {} cluster : {}".format(uuid, cluster_name))
            return uuid

        except UserError:
            raise
        except Exception as err:
            logger.warn("Error identified: {} ".format(str(err)))
            logger.warn("UUID is None. Not able to find any cluster")
            return None

    def get_stream_id(self):
        logger.debug("Finding the stream id for provided cluster name")
        uuid = self.get_replication_uuid()
        if uuid is None:
            return None
        cluster_name = self.parameters.stg_cluster_name

        stdout, stderr, exit_code = self.run_couchbase_command(
            "get_stream_id",
            source_hostname=self.source_config.couchbase_src_host,
            source_port=self.source_config.couchbase_src_port,
            source_username=self.parameters.xdcr_admin,
            source_password=self.parameters.xdcr_admin_password,
            cluster_name=cluster_name,
        )

        logger.debug(stdout)
        logger.debug(uuid)
        if exit_code != 0 or stdout is None or stdout == "":
            logger.debug("No stream ID identified")
            return None
        else:
            stream_id = re.findall(
                r"(?<=stream id:\s){}.*".format(uuid), stdout
            )
            logger.debug("Stream id found: {}".format(stream_id))
            return stream_id

    def delete_replication(self):
        logger.debug("Deleting replication...")
        stream_id = self.get_stream_id()
        cluster_name = self.parameters.stg_cluster_name
        logger.debug(
            "stream_id: {} and cluster_name : {}".format(
                stream_id, cluster_name
            )
        )
        if stream_id is None or stream_id == "":
            logger.debug("No Replication is found to delete.")
            return False, cluster_name

        for id in stream_id:
            stdout, stderr, exit_code = self.run_couchbase_command(
                "delete_replication",
                source_hostname=self.source_config.couchbase_src_host,
                source_port=self.source_config.couchbase_src_port,
                source_username=self.parameters.xdcr_admin,
                source_password=self.parameters.xdcr_admin_password,
                cluster_name=cluster_name,
                id=id,
            )

            if exit_code != 0:
                logger.warn("stream_id: {} deletion failed".format(id))
            else:
                logger.debug("stream_id: {} deletion succeeded".format(id))
        return True, cluster_name

    def get_ip(self):
        cmd = CommandFactory.get_ip_of_hostname()
        stdout, stderr, exit_code = utilities.execute_bash(
            self.connection, cmd
        )
        logger.debug("IP is {}".format(stdout))
        return stdout.split()

    def setup_replication(self):
        uuid = self.get_replication_uuid()

        if uuid is None:
            logger.info("Setting up XDRC remote cluster")
            self.xdcr_setup()

        streams_id = self.get_stream_id()

        if streams_id is not None:
            alredy_replicated_buckets = [
                m.group(1)
                for m in (re.match(r"\S*/(\S*)/\S*", x) for x in streams_id)
                if m
            ]
        else:
            alredy_replicated_buckets = []

        config_setting = self.staged_source.parameters.config_settings_prov

        if len(config_setting) > 0:
            bucket_list = [
                config_bucket["bucketName"] for config_bucket in config_setting
            ]
        else:
            bucket_details_source = self.source_bucket_list()
            bucket_list = helper_lib.filter_bucket_name_from_json(
                bucket_details_source
            )

        logger.debug("Bucket list to create replication for")
        logger.debug(bucket_list)
        logger.debug("Already replicated buckets")
        logger.debug(alredy_replicated_buckets)

        for bkt_name in bucket_list:
            if bkt_name not in alredy_replicated_buckets:
                if int(self.repository.version.split(".")[0]) >= 7:
                    logger.debug(f"bucket_name: {bkt_name}")
                    stdout, _, _ = self.run_couchbase_command(
                        couchbase_command="get_scope_list_expect",
                        base_path=helper_lib.get_base_directory_of_given_path(
                            self.repository.cb_shell_path
                        ),
                        hostname=self.source_config.couchbase_src_host,
                        port=self.source_config.couchbase_src_port,
                        username=self.staged_source.parameters.xdcr_admin,
                        password=self.staged_source.parameters.xdcr_admin_password,  # noqa E501
                        bucket_name=bkt_name,
                    )
                    json_scope_data = json.loads(stdout)
                    logger.debug(f"json_scope_data={json_scope_data}")
                    for s in json_scope_data["scopes"]:
                        scope_name = s["name"]
                        if scope_name == "_default":
                            continue
                        # create scope
                        self.run_couchbase_command(
                            couchbase_command="create_scope_expect",
                            base_path=helper_lib.get_base_directory_of_given_path(  # noqa E501
                                self.repository.cb_shell_path
                            ),
                            scope_name=scope_name,
                            bucket_name=bkt_name,
                        )
                        collection_list = s["collections"]
                        for c in collection_list:
                            collection_name = c["name"]
                            if collection_name == "_default":
                                continue
                            # create collection
                            self.run_couchbase_command(
                                couchbase_command="create_collection_expect",
                                base_path=helper_lib.get_base_directory_of_given_path(  # noqa E501
                                    self.repository.cb_shell_path
                                ),
                                scope_name=scope_name,
                                bucket_name=bkt_name,
                                collection_name=collection_name,
                            )

                logger.debug("Creating replication for {}".format(bkt_name))
                self.xdcr_replicate(bkt_name, bkt_name)
            else:
                logger.debug(
                    "Bucket {} replication already configured".format(bkt_name)
                )
