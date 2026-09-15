#
# Copyright (c) 2020-2024 by Delphix. All rights reserved.
#

##############################################################################
"""
CommandFactory class contains all commands required to perform couchbase and
OS related operations
These are a list of commands which are being used in this project. Have
segregated both types of commands into two
classes DatabaseCommand and OSCommand. CommandFactory is the actual class
through which the command string will be
returned. In the last section of this file, we have created small tests for
all these commands with dummy values.
Through which we can see the actual command is going to execute. All methods
are decorated to @staticmethod,
so no need to create an object of the class, we can use the direct class name
to use any command method.
"""
##############################################################################


import logging
import urllib.parse

logger = logging.getLogger(__name__)


class OSCommand(object):
    def __init__(self):
        pass

    @staticmethod
    def find_binary_path(**kwargs):
        return "echo $COUCHBASE_PATH"

    @staticmethod
    def find_install_path(binary_path, **kwargs):
        return "find {binary_path} -name couchbase-server".format(
            binary_path=binary_path
        )

    @staticmethod
    def find_shell_path(binary_path, **kwargs):
        return "find {binary_path} -name couchbase-cli".format(
            binary_path=binary_path
        )

    @staticmethod
    def get_process():
        return "ps -ef"

    @staticmethod
    def make_directory(directory_path, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} mkdir -p {directory_path}".format(
                uid=uid, directory_path=directory_path
            )
        else:
            return "mkdir -p {directory_path}".format(
                directory_path=directory_path
            )

    @staticmethod
    def change_permission(path, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} chmod -R 775 {path}".format(
                uid=uid, path=path
            )
        else:
            return "chmod -R 775 {path}".format(path=path)

    @staticmethod
    def get_config_directory(mount_path, **kwargs):
        return "{mount_path}/.delphix".format(mount_path=mount_path)

    @staticmethod
    def read_file(filename, **kwargs):
        return "cat {filename}".format(filename=filename)

    @staticmethod
    def check_file(file_path, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} [ -f {file_path} ] && echo 'Found'".format(
                file_path=file_path, uid=uid
            )
        else:
            return "[ -f {file_path} ] && echo 'Found'".format(
                file_path=file_path
            )

    @staticmethod
    def write_file(filename, data, sudo=False, uid=None, **kwargs):
        if sudo:
            return f"sudo -u \#{uid} echo {data} > {filename}"
        else:
            return "echo {data} > {filename}".format(
                filename=filename, data=data
            )

    @staticmethod
    def get_ip_of_hostname(**kwargs):
        return "hostname -I"

    @staticmethod
    def check_directory(dir_path, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} [ -d {dir_path} ] && echo 'Found'".format(
                dir_path=dir_path, uid=uid
            )
        else:
            return "[ -d {dir_path} ] && echo 'Found'".format(
                dir_path=dir_path
            )

    @staticmethod
    def delete_file(filename, **kwargs):
        return "rm  -f  {filename}".format(filename=filename)

    @staticmethod
    def delete_dir(dirname, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} rm  -rf  {dirname}".format(
                dirname=dirname, uid=uid
            )
        else:
            return "rm  -rf  {dirname}".format(dirname=dirname)

    @staticmethod
    def os_mv(srcname, trgname, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} mv {srcname} {trgname}".format(
                srcname=srcname, trgname=trgname, uid=uid
            )
        else:
            return "mv {srcname} {trgname}".format(
                srcname=srcname, trgname=trgname
            )

    @staticmethod
    def os_cp(srcname, trgname, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} cp {srcname} {trgname}".format(
                srcname=srcname, trgname=trgname, uid=uid
            )
        else:
            return "cp {srcname} {trgname}".format(
                srcname=srcname, trgname=trgname
            )

    @staticmethod
    def os_cpr(srcname, trgname, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} cp -r {srcname} {trgname}".format(
                srcname=srcname, trgname=trgname, uid=uid
            )
        else:
            return "cp -r {srcname} {trgname}".format(
                srcname=srcname, trgname=trgname
            )

    @staticmethod
    def os_ls(dir_path, sudo=False, uid=None, **kwargs):
        if sudo:
            return f"sudo -u \#{uid} ls {dir_path}"
        else:
            return f"ls {dir_path}"

    @staticmethod
    def get_dlpx_bin(**kwargs):
        return "echo $DLPX_BIN_JQ"

    @staticmethod
    def unmount_file_system(mount_path, **kwargs):
        if "options" in kwargs:
            options = kwargs.pop("options")
        else:
            options = ""
        return "sudo /bin/umount {options} {mount_path}".format(
            mount_path=mount_path, options=options
        )

    @staticmethod
    def whoami(**kwargs):
        return "id"

    @staticmethod
    def sed(filename, regex, sudo=False, uid=None, **kwargs):
        if sudo:
            return 'sudo -u \#{uid} sed -i -e "{regex}" {filename}'.format(
                regex=regex, filename=filename, uid=uid
            )
        else:
            return 'sed -i -e "{}" {}'.format(regex, filename)

    @staticmethod
    def cat(path, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{uid} cat {path}".format(path=path, uid=uid)
        else:
            return "cat {path}".format(path=path)

    @staticmethod
    def df(path, sudo=False, uid=None, **kwargs):
        if sudo:
            return f"sudo -u \#{uid} df -h {path}"
        else:
            return f"df -h {path}"

    @staticmethod
    def mount(sudo=False, uid=None, **kwargs):
        return "mount"

    @staticmethod
    def resolve_name(hostname, **kwargs):
        return (
            "getent ahostsv4 {hostname} | grep STREAM | head -n 1 | "
            "cut -d ' ' -f 1".format(hostname=hostname)
        )

    @staticmethod
    def du(mount_path: str, sudo=False, uid=None, **kwargs) -> str:
        """
        Returns command string to get size of dataset.

        :param mount_path: The path whose size is to be calculated

        :return: The du command string
        """
        if sudo:
            return (
                f"sudo -u \#{uid} du -s --block-size=1 --apparent-size "
                f"{mount_path}"
            )
        else:
            return f"du -s --block-size=1 --apparent-size {mount_path}"


class DatabaseCommand(object):
    def __init__(self):
        pass

    @staticmethod
    def get_parent_expect_block():
        exp_block = """
            set timeout 10
            match_max -d 5000000
            log_user 0
            {command_specific_operations}
            lassign [wait] pid spawnid os_error_flag value

            if {{$os_error_flag == 0}} {{
                puts "DLPX_EXPECT_EXIT_CODE: $value"
            }} else {{
                puts "errno: $value"
            }}
            set output $expect_out(buffer)
            puts $output
        """
        return exp_block

    @staticmethod
    def start_couchbase(install_path, sudo=False, uid=None, **kwargs):
        if sudo:
            return (
                "sudo -u \#{} {install_path} \-- -noinput -detached .".format(
                    uid, install_path=install_path
                )
            )
        else:
            return "{install_path} \-- -noinput -detached .".format(
                install_path=install_path
            )

    @staticmethod
    def get_version(install_path):
        return "{install_path} --version".format(install_path=install_path)

    @staticmethod
    def get_ids(install_path):
        return "ls -n {install_path}".format(install_path=install_path)

    @staticmethod
    def get_data_directory(couchbase_base_dir):
        return (
            "cat {couchbase_base_dir}/etc/couchbase/static_config|grep "
            "path_config_datadir".format(couchbase_base_dir=couchbase_base_dir)
        )

    @staticmethod
    def stop_couchbase(install_path, sudo=False, uid=None, **kwargs):
        if sudo:
            return "sudo -u \#{} {install_path} -k".format(
                uid, install_path=install_path
            )
        else:
            return "{install_path} -k".format(install_path=install_path)

    @staticmethod
    def cluster_init(
        shell_path,
        hostname,
        port,
        username,
        cluster_ramsize,
        cluster_name,
        cluster_index_ramsize,
        cluster_fts_ramsize,
        cluster_eventing_ramsize,
        cluster_analytics_ramsize,
        additional_services,
        **kwargs,
    ):
        return (
            "{shell_path} cluster-init --cluster {hostname}:{port} "
            "--cluster-username {username} --cluster-password $password "
            "--cluster-ramsize {cluster_ramsize} --cluster-name "
            "{cluster_name} --cluster-index-ramsize {cluster_index_ramsize}"
            "  --cluster-fts-ramsize {cluster_fts_ramsize}  "
            "--cluster-eventing-ramsize {cluster_eventing_ramsize} "
            "--cluster-analytics-ramsize {cluster_analytics_ramsize} "
            "--services data,index,{additional_services}".format(
                shell_path=shell_path,
                hostname=hostname,
                username=username,
                port=port,
                cluster_ramsize=cluster_ramsize,
                cluster_name=cluster_name,
                cluster_index_ramsize=cluster_index_ramsize,
                cluster_fts_ramsize=cluster_fts_ramsize,
                cluster_eventing_ramsize=cluster_eventing_ramsize,
                cluster_analytics_ramsize=cluster_analytics_ramsize,
                additional_services=additional_services,
            )
        )

    @staticmethod
    def cluster_init_rest_expect(
        shell_path,
        hostname,
        port,
        username,
        cluster_ramsize,
        cluster_name,
        cluster_index_ramsize,
        cluster_fts_ramsize,
        cluster_eventing_ramsize,
        cluster_analytics_ramsize,
        additional_services,
        **kwargs,
    ):
        payload_data = {
            "hostname": "127.0.0.1",
            "username": username,
            "password": kwargs.get("password"),
            "port": "SAME",
            "memoryQuota": cluster_ramsize,
            "clusterName": cluster_name,
            "indexMemoryQuota": cluster_index_ramsize,
            "ftsMemoryQuota": cluster_fts_ramsize,
            "services": f"data,index,{additional_services}",
            "indexerStorageMode": kwargs.get("indexerStorageMode"),
            "afamily": "ipv4",
            "afamilyOnly": "false",
            "nodeEncryption": "off",
        }
        if cluster_eventing_ramsize is not None:
            payload_data["eventingMemoryQuota"] = cluster_eventing_ramsize
        if cluster_analytics_ramsize is not None:
            payload_data["cbasMemoryQuota"] = cluster_analytics_ramsize

        payload_data["services"] = (
            payload_data["services"]
            .replace("data", "kv")
            .replace("query", "n1ql")
        )
        payload_string = urllib.parse.urlencode(payload_data)
        command = (
            f'echo "$PAYLOAD_SECRET" | curl -d @- -X POST '
            f"http://127.0.0.1:{port}/clusterInit -u {username}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            set timeout -1
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": "/tmp/run_shell.sh",
            "SHELL_DATA": command,
            "PAYLOAD_SECRET": payload_string,
        }
        return expect_block, env_vars

    @staticmethod
    def cluster_setting(
        shell_path,
        hostname,
        port,
        username,
        cluster_ramsize,
        cluster_name,
        cluster_index_ramsize,
        cluster_fts_ramsize,
        cluster_eventing_ramsize,
        cluster_analytics_ramsize,
        **kwargs,
    ):
        return (
            "{shell_path} setting-cluster -c {hostname}:{port} -u "
            "{username} -p $password --cluster-ramsize {cluster_ramsize} "
            "--cluster-name {cluster_name} "
            "--cluster-index-ramsize {cluster_index_ramsize} "
            "--cluster-fts-ramsize {cluster_fts_ramsize} "
            "--cluster-eventing-ramsize {cluster_eventing_ramsize} "
            "--cluster-analytics-ramsize "
            "{cluster_analytics_ramsize}".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                cluster_ramsize=cluster_ramsize,
                cluster_name=cluster_name,
                cluster_index_ramsize=cluster_index_ramsize,
                cluster_fts_ramsize=cluster_fts_ramsize,
                cluster_eventing_ramsize=cluster_eventing_ramsize,
                cluster_analytics_ramsize=cluster_analytics_ramsize,
            )
        )

    @staticmethod
    def cluster_setting_expect(
        shell_path,
        hostname,
        port,
        username,
        cluster_ramsize,
        cluster_name,
        cluster_index_ramsize,
        cluster_fts_ramsize,
        cluster_eventing_ramsize,
        cluster_analytics_ramsize,
        **kwargs,
    ):
        command = (
            f"{shell_path} setting-cluster -c {hostname}:{port} -u "
            f"{username} --password --cluster-ramsize "
            f"{cluster_ramsize} --cluster-name {cluster_name} "
            f"--cluster-index-ramsize {cluster_index_ramsize} "
            f"--cluster-fts-ramsize {cluster_fts_ramsize} "
            f"--cluster-eventing-ramsize {cluster_eventing_ramsize} "
            f"--cluster-analytics-ramsize {cluster_analytics_ramsize}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def xdcr_setup(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        hostname,
        port,
        username,
        cluster_name,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-setup --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --create --xdcr-hostname {hostname}:{port} "
            "--xdcr-username {username} --xdcr-password $password "
            "--xdcr-cluster-name {cluster_name}".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                hostname=hostname,
                port=port,
                username=username,
                cluster_name=cluster_name,
            )
        )

    @staticmethod
    def xdcr_setup_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        hostname,
        port,
        username,
        cluster_name,
        **kwargs,
    ):
        payload_data = {
            "username": username,
            "password": kwargs.get("password"),
            "hostname": f"{hostname}:{port}",
            "name": cluster_name,
            "demandEncryption": 0,
        }
        payload_string = urllib.parse.urlencode(payload_data)
        command = (
            f'echo "$PAYLOAD_SECRET" | curl -d @- -X POST '
            f"http://{source_hostname}:{source_port}/pools/default/"
            f"remoteClusters -u {source_username}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            set timeout -1
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {
            "CB_PWD": kwargs.get("source_password"),
            "CB_CMD": "/tmp/run_shell.sh",
            "SHELL_DATA": command,
            "PAYLOAD_SECRET": payload_string,
        }
        return expect_block, env_vars

    @staticmethod
    def xdcr_replicate(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        source_bucket_name,
        target_bucket_name,
        cluster_name,
        hostname,
        port,
        username,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-replicate --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --create --xdcr-from-bucket "
            "{source_bucket_name} --xdcr-to-bucket {target_bucket_name} "
            "--xdcr-cluster-name {cluster_name}".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                source_bucket_name=source_bucket_name,
                target_bucket_name=target_bucket_name,
                cluster_name=cluster_name,
            )
        )

    @staticmethod
    def xdcr_replicate_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        source_bucket_name,
        target_bucket_name,
        cluster_name,
        hostname,
        port,
        username,
        **kwargs,
    ):
        command = (
            f"{shell_path} xdcr-replicate --cluster {source_hostname}:"
            f"{source_port} --username {source_username} --password "
            f"--create --xdcr-from-bucket {source_bucket_name} "
            f"--xdcr-to-bucket {target_bucket_name} "
            f"--xdcr-cluster-name {cluster_name}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def get_replication_uuid(
        shell_path, source_hostname, source_port, source_username, **kwargs
    ):
        return (
            "{shell_path} xdcr-setup --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --list".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
            )
        )

    @staticmethod
    def get_replication_uuid_expect(
        shell_path, source_hostname, source_port, source_username, **kwargs
    ):
        command = (
            f"{shell_path} xdcr-setup --cluster {source_hostname}:"
            f"{source_port} --username {source_username} --password "
            f"--list"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def get_stream_id(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        cluster_name,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-replicate --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --xdcr-cluster-name {cluster_name} "
            "--list".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                cluster_name=cluster_name,
            )
        )

    @staticmethod
    def get_stream_id_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        cluster_name,
        **kwargs,
    ):
        command = (
            f"{shell_path} xdcr-replicate --cluster {source_hostname}:"
            f"{source_port} --username {source_username} "
            f"--password --xdcr-cluster-name {cluster_name} --list"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def pause_replication(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        cluster_name,
        id,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-replicate --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --xdcr-cluster-name {cluster_name} "
            "--pause --xdcr-replicator={id}".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                cluster_name=cluster_name,
                id=id,
            )
        )

    @staticmethod
    def pause_replication_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        cluster_name,
        id,
        **kwargs,
    ):
        command = (
            f"{shell_path} xdcr-replicate --cluster {source_hostname}:"
            f"{source_port} --username {source_username} "
            f"--password --xdcr-cluster-name {cluster_name} "
            f"--pause --xdcr-replicator={id}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def resume_replication(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        cluster_name,
        id,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-replicate --cluster {source_hostname}:"
            "{source_port}  --username {source_username} --password "
            "$source_password --xdcr-cluster-name {cluster_name} "
            "--resume --xdcr-replicator={id}".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                cluster_name=cluster_name,
                id=id,
            )
        )

    @staticmethod
    def resume_replication_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        cluster_name,
        id,
        **kwargs,
    ):
        command = (
            f"{shell_path} xdcr-replicate --cluster {source_hostname}:"
            f"{source_port}  --username {source_username} --password "
            f"--xdcr-cluster-name {cluster_name} --resume "
            f"--xdcr-replicator={id}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def delete_replication(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        id,
        cluster_name,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-replicate --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --delete --xdcr-replicator {id} "
            "--xdcr-cluster-name {cluster_name}".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                id=id,
                cluster_name=cluster_name,
            )
        )

    @staticmethod
    def delete_replication_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        id,
        cluster_name,
        **kwargs,
    ):
        command = (
            f"{shell_path} xdcr-replicate --cluster {source_hostname}:"
            f"{source_port} --username {source_username} --password "
            f"--delete --xdcr-replicator {id} --xdcr-cluster-name "
            f"{cluster_name}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def xdcr_delete(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        hostname,
        port,
        username,
        cluster_name,
        **kwargs,
    ):
        return (
            "{shell_path} xdcr-setup --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$source_password --delete --xdcr-hostname {hostname}:{port} "
            "--xdcr-username {username} --xdcr-password $password "
            "--xdcr-cluster-name {cluster_name}".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
                hostname=hostname,
                port=port,
                username=username,
                cluster_name=cluster_name,
            )
        )

    @staticmethod
    def xdcr_delete_expect(
        shell_path,
        source_hostname,
        source_port,
        source_username,
        hostname,
        port,
        username,
        cluster_name,
        **kwargs,
    ):
        command = (
            f"curl -X DELETE http://{source_hostname}:{source_port}/"
            f"pools/default/remoteClusters/{cluster_name} -u "
            f"{source_username}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            set timeout -1
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("source_password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def get_source_bucket_list(
        shell_path, source_hostname, source_port, source_username, **kwargs
    ):
        return (
            "{shell_path} bucket-list --cluster {source_hostname}:"
            "{source_port} --username {source_username} --password "
            "$password -o json".format(
                shell_path=shell_path,
                source_hostname=source_hostname,
                source_port=source_port,
                source_username=source_username,
            )
        )

    @staticmethod
    def get_source_bucket_list_expect(
        shell_path, source_hostname, source_port, source_username, **kwargs
    ):
        command = (
            f"{shell_path} bucket-list --cluster {source_hostname}:"
            f"{source_port} --username {source_username} --password "
            f"-o json"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                            expect {
                                -re "Enter password:.*" {
                                    send "${env(CB_PWD)}\n"
                                    exp_continue
                                }
                                timeout {
                                    puts "EXPECT SCRIPT TIMEOUT"
                                    exit 2
                                }
                            }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def get_server_list(shell_path, hostname, port, username, **kwargs):
        return (
            "{shell_path} server-list --cluster {hostname}:{port} "
            "--username {username} --password $password".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
            )
        )

    @staticmethod
    def get_server_list_expect(shell_path, hostname, port, username, **kwargs):
        command = (
            f"{shell_path} server-list --cluster {hostname}:{port} "
            f"--username {username} --password"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
            expect {
                -re "Enter password:.*" {
                    send "${env(CB_PWD)}\n"
                    exp_continue
                }
                timeout {
                    puts "EXPECT SCRIPT TIMEOUT"
                    exit 2
                }
            }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def node_init(shell_path, port, username, data_path, **kwargs):
        return (
            "{shell_path} node-init  --cluster 127.0.0.1:{port} "
            "--username {username} --password $password "
            "--node-init-data-path {data_path}  --node-init-index-path "
            "{data_path} --node-init-analytics-path {data_path}  "
            "--node-init-hostname 127.0.0.1".format(
                shell_path=shell_path,
                port=port,
                username=username,
                data_path=data_path,
            )
        )

    @staticmethod
    def node_init_expect(shell_path, port, username, data_path, **kwargs):
        command = (
            f"{shell_path} node-init  --cluster 127.0.0.1:{port} "
            f"--username {username} --password --node-init-data-path "
            f"{data_path}  --node-init-index-path {data_path} "
            f"--node-init-analytics-path {data_path}  "
            f"--node-init-hostname 127.0.0.1"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                    expect {
                        -re "Enter password:.*" {
                            send "${env(CB_PWD)}\n"
                            exp_continue
                        }
                        timeout {
                            puts "EXPECT SCRIPT TIMEOUT"
                            exit 2
                        }
                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def bucket_edit(
        shell_path,
        hostname,
        port,
        username,
        bucket_name,
        flush_value,
        **kwargs,
    ):
        return (
            "{shell_path} bucket-edit --cluster {hostname}:{port} "
            "--username {username} --password $password "
            "--bucket={bucket_name} --enable-flush {flush_value}".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                bucket_name=bucket_name,
                flush_value=flush_value,
            )
        )

    @staticmethod
    def bucket_edit_expect(
        shell_path,
        hostname,
        port,
        username,
        bucket_name,
        flush_value,
        **kwargs,
    ):
        command = (
            f"{shell_path} bucket-edit --cluster {hostname}:{port} "
            f"--username {username} --password --bucket={bucket_name} "
            f"--enable-flush {flush_value}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                            expect {
                                -re "Enter password:.*" {
                                    send "${env(CB_PWD)}\n"
                                    exp_continue
                                }
                                timeout {
                                    puts "EXPECT SCRIPT TIMEOUT"
                                    exit 2
                                }
                            }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def bucket_edit_ramquota(
        shell_path, hostname, port, username, bucket_name, ramsize, **kwargs
    ):
        return (
            "{shell_path} bucket-edit --cluster {hostname}:{port} "
            "--username {username} --password $password "
            "--bucket={bucket_name} --bucket-ramsize {ramsize}".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                bucket_name=bucket_name,
                ramsize=ramsize,
            )
        )

    @staticmethod
    def bucket_edit_ramquota_expect(
        shell_path, hostname, port, username, bucket_name, ramsize, **kwargs
    ):
        command = (
            f"{shell_path} bucket-edit --cluster {hostname}:{port} "
            f"--username {username} --password --bucket={bucket_name} "
            f"--bucket-ramsize {ramsize}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def bucket_delete(
        shell_path, hostname, port, username, bucket_name, **kwargs
    ):
        return (
            "{shell_path} bucket-delete --cluster {hostname}:{port} "
            "--username {username} --password $password  "
            "--bucket={bucket_name}".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                bucket_name=bucket_name,
            )
        )

    @staticmethod
    def bucket_delete_expect(
        shell_path, hostname, port, username, bucket_name, **kwargs
    ):
        command = (
            f"{shell_path} bucket-delete --cluster {hostname}:{port} "
            f"--username {username} --password --bucket={bucket_name}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def bucket_flush(
        shell_path, hostname, port, username, bucket_name, **kwargs
    ):
        return (
            "echo 'Yes' | {shell_path}  bucket-flush --cluster "
            "{hostname}:{port} --username {username} --password $password "
            "--bucket={bucket_name}".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                bucket_name=bucket_name,
            )
        )

    @staticmethod
    def bucket_flush_expect(
        shell_path, hostname, port, username, bucket_name, **kwargs
    ):
        command = (
            f"{shell_path}  bucket-flush --cluster {hostname}:{port} "
            f"--username {username} --password --bucket={bucket_name}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        -re "Running this command will totally PURGE database data from disk. Do you really want to do it? (Yes/No).*" {
                                            send "Yes\n"
                                            set timeout -1
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""  # noqa
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def bucket_create(
        shell_path,
        hostname,
        port,
        username,
        bucket_name,
        ramsize,
        evictionpolicy,
        bucket_type,
        bucket_compression,
        **kwargs,
    ):
        return (
            "{shell_path} bucket-create --cluster 127.0.0.1:{port} "
            "--username {username} --password $password --bucket "
            "{bucket_name} --bucket-type {bucket_type} --bucket-ramsize "
            "{ramsize} --bucket-replica 0 --bucket-eviction-policy "
            "{evictionpolicy} {bucket_compression} --conflict-resolution "
            "sequence --wait".format(
                shell_path=shell_path,
                port=port,
                username=username,
                bucket_name=bucket_name,
                ramsize=ramsize,
                evictionpolicy=evictionpolicy,
                bucket_type=bucket_type,
                bucket_compression=bucket_compression,
            )
        )

    @staticmethod
    def bucket_create_expect(
        shell_path,
        hostname,
        port,
        username,
        bucket_name,
        ramsize,
        evictionpolicy,
        bucket_type,
        bucket_compression,
        **kwargs,
    ):
        command = (
            f"{shell_path} bucket-create --cluster 127.0.0.1:{port} "
            f"--username {username} --password --bucket {bucket_name} "
            f"--bucket-type {bucket_type} --bucket-ramsize {ramsize} "
            f"--bucket-replica 0 --bucket-eviction-policy "
            f"{evictionpolicy} {bucket_compression} "
            f"--conflict-resolution sequence --wait"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def bucket_list(shell_path, hostname, port, username, **kwargs):
        return (
            "{shell_path} bucket-list --cluster {hostname}:{port} "
            "--username {username} --password $password -o json".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
            )
        )

    @staticmethod
    def bucket_list_expect(shell_path, hostname, port, username, **kwargs):
        command = (
            f"{shell_path} bucket-list --cluster {hostname}:{port}"
            f" --username {username} --password -o json"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                    expect {
                        -re "Enter password:.*" {
                            send "${env(CB_PWD)}\n"
                            exp_continue
                        }
                        timeout {
                            puts "EXPECT SCRIPT TIMEOUT"
                            exit 2
                        }
                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def get_indexes_name(hostname, port, username, **kwargs):
        return (
            "curl {username}:$password@{hostname}:{port}/indexStatus".format(
                hostname=hostname, port=port, username=username
            )
        )

    @staticmethod
    def get_indexes_name_expect(hostname, port, username, **kwargs):
        command = f"curl -u {username} {hostname}:{port}/indexStatus"
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                            expect {
                                -re "Enter host password for user.*" {
                                    send "${env(CB_PWD)}\n"
                                    exp_continue
                                }
                                timeout {
                                    puts "EXPECT SCRIPT TIMEOUT"
                                    exit 2
                                }
                            }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def get_scope_list_expect(hostname, port, username, **kwargs):
        command = (
            f"curl -u {username} {hostname}:{port}/pools/default/"
            f"buckets/{kwargs.get('bucket_name')}/scopes"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def create_scope_expect(base_path, hostname, port, username, **kwargs):
        command = f"{base_path}/cbq -e {hostname}:{port} -u {username} -q=true"
        cb_query = (
            f"CREATE SCOPE `{kwargs.get('bucket_name')}`."
            f"{kwargs.get('scope_name')};"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter Password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            -re ".*ERROR 100 :.*" {
                                                puts "Error occured"
                                                send "\x04"
                                            }
                                                -re "(.|\n)*cbq>(.|\n)*" {
                                                send "${env(CB_QUERY)};\n"
                                                expect -re "\n(.|\n)*"
                                                send "\x04"
                                                expect eof
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        logger.debug(f"cb_query: {cb_query}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": command,
            "CB_QUERY": cb_query,
        }
        return expect_block, env_vars

    @staticmethod
    def create_collection_expect(
        base_path, hostname, port, username, **kwargs
    ):
        command = f"{base_path}/cbq -e {hostname}:{port} -u {username} -q=true"
        cb_query = (
            f"CREATE COLLECTION `{kwargs.get('bucket_name')}`."
            f"{kwargs.get('scope_name')}."
            f"{kwargs.get('collection_name')};"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter Password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            -re ".*ERROR 100 :.*" {
                                                puts "Error occured"
                                                send "\x04"
                                            }
                                                -re "(.|\n)*cbq>(.|\n)*" {
                                                send "${env(CB_QUERY)};\n"
                                                expect -re "\n(.|\n)*"
                                                send "\x04"
                                                expect eof
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        logger.debug(f"cb_query: {cb_query}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": command,
            "CB_QUERY": cb_query,
        }
        return expect_block, env_vars

    @staticmethod
    def get_backup_bucket_list(path, sudo=False, uid=None, **kwargs):
        if sudo:
            return (
                "sudo -u \#{uid} find {path} -name bucket-config.json".format(
                    path=path, uid=uid
                )
            )
        else:
            return "find {path} -name bucket-config.json".format(path=path)

    @staticmethod
    def build_index(base_path, hostname, port, username, index_def, **kwargs):
        return (
            "{base_path}/cbq -e {hostname}:{port} -u {username} "
            "-p $password -q=true -s='{index_def}'".format(
                base_path=base_path,
                hostname=hostname,
                port=port,
                username=username,
                index_def=index_def,
            )
        )

    @staticmethod
    def build_index_expect(
        base_path, hostname, port, username, index_def, **kwargs
    ):
        command = f"{base_path}/cbq -e {hostname}:{port} -u {username} -q=true"
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter Password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        -re ".*ERROR 100 :.*" {
                                            puts "Error occured"
                                            send "\x04"
                                        }
                                            -re "(.|\n)*cbq>(.|\n)*" {
                                            send "${env(CB_QUERY)};\n"
                                            expect -re "\n(.|\n)*"
                                            send "\x04"
                                            expect eof
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        logger.debug(f"cb_query: {index_def}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": command,
            "CB_QUERY": index_def,
        }
        return expect_block, env_vars

    @staticmethod
    def check_index_build(base_path, hostname, port, username, **kwargs):
        return (
            "{base_path}/cbq -e {hostname}:{port} -u {username} "
            '-p $password -q=true -s="SELECT COUNT(*) as unbuilt '
            "FROM system:indexes WHERE state <> 'online'\"".format(
                base_path=base_path,
                hostname=hostname,
                port=port,
                username=username,
            )
        )

    @staticmethod
    def check_index_build_expect(
        base_path, hostname, port, username, **kwargs
    ):
        command = f"{base_path}/cbq -e {hostname}:{port} -u {username} -q=true"
        cb_query = (
            "SELECT COUNT(*) as unbuilt FROM system:indexes WHERE "
            "state <> 'online'"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                        expect {
                                            -re "Enter Password:.*" {
                                                send "${env(CB_PWD)}\n"
                                                exp_continue
                                            }
                                            -re ".*ERROR 100 :.*" {
                                                puts "Error occured"
                                                send "\x04"
                                            }
                                                -re "(.|\n)*cbq>(.|\n)*" {
                                                send "${env(CB_QUERY)};\n"
                                                expect -re "\n(.|\n)*"
                                                send "\x04"
                                                expect eof
                                            }
                                            timeout {
                                                puts "EXPECT SCRIPT TIMEOUT"
                                                exit 2
                                            }
                                        }"""
        )
        logger.debug(f"command: {command}")
        logger.debug(f"cb_query: {cb_query}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": command,
            "CB_QUERY": cb_query,
        }
        return expect_block, env_vars

    @staticmethod
    def cb_backup_full(
        base_path,
        backup_location,
        backup_repo,
        hostname,
        port,
        username,
        csv_bucket_list,
        sudo,
        uid,
        skip,
        **kwargs,
    ):
        if sudo:
            return (
                "sudo -u \#{uid} {base_path}/cbbackupmgr restore "
                "--archive {backup_location} --repo {backup_repo} "
                "--cluster couchbase://{hostname}:{port} --username "
                "{username} --password $password --force-updates {skip} "
                "--no-progress-bar --include-buckets "
                "{csv_bucket_list}".format(
                    base_path=base_path,
                    backup_location=backup_location,
                    backup_repo=backup_repo,
                    hostname=hostname,
                    port=port,
                    username=username,
                    csv_bucket_list=csv_bucket_list,
                    uid=uid,
                    skip=skip,
                )
            )
        else:
            return (
                "{base_path}/cbbackupmgr restore --archive "
                "{backup_location} --repo {backup_repo} --cluster "
                "couchbase://{hostname}:{port} --username {username} "
                "--password $password --force-updates {skip} "
                "--no-progress-bar --include-buckets "
                "{csv_bucket_list}".format(
                    base_path=base_path,
                    backup_location=backup_location,
                    backup_repo=backup_repo,
                    hostname=hostname,
                    port=port,
                    username=username,
                    csv_bucket_list=csv_bucket_list,
                    skip=skip,
                )
            )

    @staticmethod
    def cb_backup_full_expect(
        base_path,
        backup_location,
        backup_repo,
        hostname,
        port,
        username,
        csv_bucket_list,
        sudo,
        uid,
        skip,
        **kwargs,
    ):
        if sudo:
            command = (
                f"sudo -u \#{uid} {base_path}/cbbackupmgr restore "
                f"--archive {backup_location} --repo {backup_repo} "
                f"--cluster couchbase://{hostname}:{port} --username "
                f"{username} --password --force-updates {skip} "
                f"--no-progress-bar --include-buckets {csv_bucket_list}"
            )
        else:
            command = (
                f"{base_path}/cbbackupmgr restore --archive "
                f"{backup_location} --repo {backup_repo} --cluster "
                f"couchbase://{hostname}:{port} --username {username} "
                f"--password --force-updates {skip} --no-progress-bar "
                f"--include-buckets {csv_bucket_list}"
            )
        if int(kwargs.get("repo_version").split(".")[0]) >= 7:
            command = f"{command} --purge"
        if kwargs.get("map_data") != "":
            command = f"{command} --map-data {kwargs.get('map_data')}"
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                            expect {
                                -re "Password:.*" {
                                    send "${env(CB_PWD)}\n"
                                    set timeout -1
                                    exp_continue
                                }
                                -re "Password for --password:.*" {
                                    send "${env(CB_PWD)}\n"
                                    set timeout -1
                                    exp_continue
                                }
                                timeout {
                                    puts "EXPECT SCRIPT TIMEOUT"
                                    exit 2
                                }
                            }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def monitor_replication(
        source_username,
        source_hostname,
        source_port,
        bucket_name,
        uuid,
        **kwargs,
    ):
        return (
            "curl --silent -u {source_username}:$password "
            "http://{source_hostname}:{source_port}/pools/default/buckets"
            "/{bucket_name}/stats/replications%2F{uuid}%2F{bucket_name}"
            "%2F{bucket_name}%2Fchanges_left".format(
                source_username=source_username,
                source_hostname=source_hostname,
                source_port=source_port,
                bucket_name=bucket_name,
                uuid=uuid,
            )
        )

    @staticmethod
    def monitor_replication_expect(
        source_username,
        source_hostname,
        source_port,
        bucket_name,
        uuid,
        **kwargs,
    ):
        command = (
            f"curl --silent -u {source_username} "
            f"http://{source_hostname}:{source_port}/pools/default/"
            f"buckets/{bucket_name}/stats/replications%2F{uuid}%2F"
            f"{bucket_name}%2F{bucket_name}%2Fchanges_left"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def couchbase_server_info(shell_path, hostname, username, port, **kwargs):
        return (
            "{shell_path} server-info --cluster {hostname}:{port} "
            "--username {username} --password $password".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
            )
        )
        # return("{shell_path}".format(shell_path=shell_path))

    @staticmethod
    def couchbase_server_info_expect(
        shell_path, hostname, username, port, **kwargs
    ):
        command = (
            f"{shell_path} server-info --cluster {hostname}:{port} "
            f"--username {username} --password"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                    expect {
                        -re "Enter password:.*" {
                            send "${env(CB_PWD)}\n"
                            exp_continue
                        }
                        timeout {
                            puts "EXPECT SCRIPT TIMEOUT"
                            exit 2
                        }
                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def rename_cluster(
        shell_path, hostname, port, username, newuser, newname, **kwargs
    ):
        return (
            "{shell_path} setting-cluster --cluster {hostname}:{port} "
            "--username {username} --password $password "
            "--cluster-username {newuser} --cluster-password $newpass "
            "--cluster-name {newname}".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                newuser=newuser,
                newname=newname,
            )
        )

    @staticmethod
    def rename_cluster_expect(
        shell_path, hostname, port, username, newname, **kwargs
    ):
        command = (
            f"curl -X POST http://{hostname}:{port}/pools/default "
            f"-d clusterName={newname} -u {username}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars

    @staticmethod
    def change_cluster_password_expect(
        shell_path, hostname, port, username, newuser, **kwargs
    ):
        payload_string = (
            f"password={kwargs.get('newpass')}&username={newuser}&port=SAME"
        )
        command = (
            f'echo "$PAYLOAD_SECRET" | curl -d @- -X POST '
            f"http://{hostname}:{port}/settings/web -u {username}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter host password for user.*" {
                                            send "${env(CB_PWD)}\n"
                                            set timeout -1
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": "/tmp/run_shell.sh",
            "SHELL_DATA": command,
            "PAYLOAD_SECRET": payload_string,
        }
        return expect_block, env_vars

    @staticmethod
    def server_add(
        shell_path, hostname, port, username, newhost, services, **kwargs
    ):
        return (
            "{shell_path} server-add --cluster {hostname}:{port} "
            "--username {username} --password $password \
            --server-add https://{newhost}:18091 --server-add-username "
            "{username} --server-add-password $password \
            --services {services} --no-ssl-verify".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
                services=services,
                newhost=newhost,
            )
        )

    @staticmethod
    def server_add_expect(
        shell_path, hostname, port, username, newhost, services, **kwargs
    ):
        if kwargs.get("new_port") == "8091":
            hostname_prefix = "http"
        else:
            hostname_prefix = "https"
        payload_data = {
            "hostname": f"{hostname_prefix}://{newhost}:"
            f"{kwargs.get('new_port')}",
            "user": username,
            "password": kwargs.get("password"),
            "services": services,
        }
        payload_data["services"] = (
            payload_data["services"]
            .replace("data", "kv")
            .replace("query", "n1ql")
        )
        payload_string = urllib.parse.urlencode(payload_data)
        command = (
            f'echo "$PAYLOAD_SECRET" | curl -d @- -X POST '
            f"{hostname}:8091/controller/addNode -u {username}"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                expect {
                                    -re "Enter host password for user.*" {
                                        send "${env(CB_PWD)}\n"
                                        set timeout -1
                                        exp_continue
                                    }
                                    timeout {
                                        puts "EXPECT SCRIPT TIMEOUT"
                                        exit 2
                                    }
                                }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {
            "CB_PWD": kwargs.get("password"),
            "CB_CMD": "/tmp/run_shell.sh",
            "SHELL_DATA": command,
            "PAYLOAD_SECRET": payload_string,
        }
        return expect_block, env_vars

    @staticmethod
    def rebalance(shell_path, hostname, port, username, **kwargs):
        return (
            "{shell_path} rebalance --cluster {hostname}:{port} "
            "--username {username} --password $password \
            --no-progress-bar".format(
                shell_path=shell_path,
                hostname=hostname,
                port=port,
                username=username,
            )
        )

    @staticmethod
    def rebalance_expect(shell_path, hostname, port, username, **kwargs):
        command = (
            f"{shell_path} rebalance --cluster {hostname}:{port} "
            f"--username {username} --password --no-progress-bar"
        )
        expect_block = DatabaseCommand.get_parent_expect_block().format(
            command_specific_operations="""eval spawn ${env(CB_CMD)}
                                    expect {
                                        -re "Enter password:.*" {
                                            send "${env(CB_PWD)}\n"
                                            set timeout -1
                                            exp_continue
                                        }
                                        timeout {
                                            puts "EXPECT SCRIPT TIMEOUT"
                                            exit 2
                                        }
                                    }"""
        )
        logger.debug(f"command: {command}")
        env_vars = {"CB_PWD": kwargs.get("password"), "CB_CMD": command}
        return expect_block, env_vars


class CommandFactory(DatabaseCommand, OSCommand):
    def __init__(self):
        DatabaseCommand.__init__(self)
        OSCommand.__init__(self)


if __name__ == "__main__":
    print("\n****Test Above Commands With Dummy Values****\n")
    install_path = "DummyInstallPath"
    binary_path = "/opt/couchbase/bin"
    shell_path = "/opt/couchbase/bin"
    hostname = "hostname"
    port = "8091"
    username = "USER"
    cluster_name = "delphix_cluster"
    cluster_ramsize = "200"
    cluster_index_ramsize = "300"
    cluster_fts_ramsize = "400"
    cluster_eventing_ramsize = "500"
    cluster_analytics_ramsize = "600"
    additional_services = "query,index,data"
    source_hostname = "source_hostname"
    source_port = "source_port"
    source_username = "source_username"
    source_bucket_name = "source_bucket_name"
    target_bucket_name = "target_bucket_name"
    uuid = "12345678"
    directory_path = "/mnt/provision/test/directory_path"
    mount_path = "/mnt/provision/mount_path"
    bucket_name = "sample"
    flush_value = "0"
    ramsize = "100"
    evictionpolicy = "evictionpolicy"
    base_path = "base_path"
    index = "index"
    index_name = "index_name"
    backup_location = "backup_location"
    backup_repo = "backup_repo"
    csv_bucket_list = "csv_bucket_list"
    filename = "filename"
    file_path = "test"
    data = "data"
    hostname = "192.168.1.14"
    dir_path = "/var/tmp"
    DLPX_BIN_JQ = "/var/tmp"
