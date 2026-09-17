#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
"""
This class contains methods for cluster related operations
This is child class of Resource and parent class of CouchbaseOperation.
"""
##############################################################################
import logging
import re

from controller.couchbase_lib._mixin_interface import MixinInterface
from controller.helper_lib import sleepForSecond
from controller.resource_builder import Resource
from db_commands.commands import CommandFactory
from db_commands.constants import ENV_VAR_KEY
from utils import utilities

logger = logging.getLogger(__name__)

# Error string on which we have to skip without raising the Exception
ALREADY_CLUSTER_INIT = (
    "Cluster is already initialized, use setting-cluster to change settings"
)


class _ClusterMixin(Resource, MixinInterface):
    def __init__(self, builder):
        super(_ClusterMixin, self).__init__(builder)

    @MixinInterface.check_attribute_error
    def generate_environment_map(self):
        env = {
            "shell_path": self.repository.cb_shell_path,
            "hostname": self.connection.environment.host.name,
            "port": self.parameters.couchbase_port,
            "username": self.parameters.couchbase_admin,
            "cluster_ramsize": self.parameters.cluster_ram_size,
            "cluster_index_ramsize": self.parameters.cluster_index_ram_size,
            "cluster_fts_ramsize": self.parameters.cluster_ftsram_size,
            "cluster_eventing_ramsize": self.parameters.cluster_eventing_ram_size,  # noqa E501
            "cluster_analytics_ramsize": self.parameters.cluster_analytics_ram_size,  # noqa E501
        }
        # MixinInterface.read_map(env)
        return env

    def _get_cluster_name(self):
        cluster_name = None
        if self.dSource:
            cluster_name = self.parameters.stg_cluster_name
        else:
            cluster_name = self.parameters.tgt_cluster_name
        return cluster_name

    def cluster_init(self):
        # Cluster initialization
        logger.debug("Cluster Initialization started")
        fts_service = self.parameters.fts_service
        # analytics_service = self.parameters.analytics_service
        eventing_service = self.parameters.eventing_service
        cluster_name = self._get_cluster_name()
        kwargs = {
            ENV_VAR_KEY: {"password": self.parameters.couchbase_admin_password}
        }
        additional_service = "query"
        if fts_service:
            additional_service = additional_service + ",fts"
        # if analytics_service:
        #     additional_service = additional_service + ",analytics"
        if eventing_service:
            additional_service = additional_service + ",eventing"

        logger.debug("additional services : {}".format(additional_service))

        def f():
            return lambda output: bool(re.search(ALREADY_CLUSTER_INIT, output))

        lambda_expr = f
        env = _ClusterMixin.generate_environment_map(self)
        env["additional_services"] = additional_service
        if int(self.repository.version.split(".")[0]) >= 7:
            env.update(kwargs[ENV_VAR_KEY])
            if "(CE)" in self.repository.version:
                env["cluster_eventing_ramsize"] = None
                env["cluster_analytics_ramsize"] = None
                env["indexerStorageMode"] = "forestdb"
            else:
                env["indexerStorageMode"] = "plasma"
            cmd, env_vars = CommandFactory.cluster_init_rest_expect(
                cluster_name=cluster_name, **env
            )
            kwargs[ENV_VAR_KEY].update(env_vars)
            stdout, stderr, exit_code = utilities.execute_expect(
                self.connection, cmd, **kwargs
            )
        else:
            cmd = CommandFactory.cluster_init(cluster_name=cluster_name, **env)
            logger.debug("Cluster init: {}".format(cmd))
            stdout, stderr, exit_code = utilities.execute_bash(
                self.connection,
                command_name=cmd,
                callback_func=lambda_expr,
                **kwargs
            )
        if re.search(r"ERROR", str(stdout)):
            if re.search(r"ERROR: Cluster is already initialized", stdout):
                logger.debug(
                    "Performing cluster setting as cluster is already "
                    "initialized"
                )
                self.cluster_setting()
            else:
                logger.error("Cluster init failed. Throwing exception")
                raise Exception(stdout)
        else:
            logger.debug("Cluster init succeeded")

        # here we should wait for indexer to start
        sleepForSecond(10)
        return [stdout, stderr, exit_code]

    def cluster_setting(self):
        logger.debug("Cluster setting process has started")
        kwargs = {
            ENV_VAR_KEY: {"password": self.parameters.couchbase_admin_password}
        }
        cluster_name = self._get_cluster_name()
        env = _ClusterMixin.generate_environment_map(self)
        env.update(kwargs[ENV_VAR_KEY])
        cmd, env_vars = CommandFactory.cluster_setting_expect(
            cluster_name=cluster_name, **env
        )
        kwargs[ENV_VAR_KEY].update(env_vars)
        stdout, stderr, exit_code = utilities.execute_expect(
            self.connection, cmd, **kwargs
        )
        if re.search(r"ERROR", str(stdout)):
            logger.error("Cluster modification failed, killing the execution")
            raise Exception(stdout)
        logger.debug("Cluster modification succeeded")
        return [stdout, stderr, exit_code]
