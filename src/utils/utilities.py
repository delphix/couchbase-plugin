#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

import logging
import random

from dlpx.virtualization import libs
from dlpx.virtualization.libs import exceptions

# logger object
logger = logging.getLogger(__name__)


def execute_bash(
    source_connection, command_name, callback_func=None, environment_vars=None
):
    """
    :param callback_func:
    :param source_connection: Connection object for the source environment
    :param command_name: Command to be search from dictionary of bash command
    :param environment_vars: Expecting environment variables which are required
     to execute the command
    :return: list of output of command, error string, exit code
    """

    if source_connection is None:
        raise exceptions.PluginScriptError("Connection object cannot be empty")

    result = libs.run_bash(
        source_connection,
        command=command_name,
        variables=environment_vars,
        use_login_shell=True,
    )

    # strip the each part of result to remove spaces from beginning
    # and last of output
    output = result.stdout.strip()
    error = result.stderr.strip()
    exit_code = result.exit_code

    # Verify the exit code of each executed command. 0 means command ran
    # successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs will
    # die and otherwise execution will continue.
    # _handle_exit_code(exit_code, error, output, callback_func)
    return [output, error, exit_code]


def execute_expect(
    source_connection, command_name, callback_func=None, environment_vars=None
):
    """
    :param callback_func:
    :param source_connection: Connection object for the source environment
    :param command_name: Command to be search from dictionary of bash command
    :param environment_vars: Expecting environment variables which are
    required to execute the command
    :return: list of output of command, error string, exit code
    """

    if source_connection is None:
        raise exceptions.PluginScriptError("Connection object cannot be empty")

    file_random_id = random.randint(1000000000, 9999999999)

    if "SHELL_DATA" in environment_vars:
        environment_vars["CB_CMD"] = environment_vars["CB_CMD"].replace(
            ".sh", f"_{file_random_id}.sh"
        )
        result = libs.run_bash(
            source_connection,
            command='echo -e "$SHELL_DATA" > $CB_CMD',
            use_login_shell=True,
            variables=environment_vars,
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        exit_code = result.exit_code

        logger.debug(f"dump_output==={output}")
        logger.debug(f"dump_error==={error}")
        logger.debug(f"dump_exit_code==={exit_code}")
        result = libs.run_bash(
            source_connection,
            command="chmod +x $CB_CMD",
            use_login_shell=True,
            variables=environment_vars,
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        exit_code = result.exit_code

        logger.debug(f"executable_output==={output}")
        logger.debug(f"executable_error==={error}")
        logger.debug(f"executable_exit_code==={exit_code}")

    file_path = f"/tmp/expect_script_{file_random_id}.exp"

    result = libs.run_bash(
        source_connection,
        command=f"echo -e '{command_name}' > {file_path}",
        use_login_shell=True,
    )
    output = result.stdout.strip()
    error = result.stderr.strip()
    exit_code = result.exit_code

    logger.debug(f"script_dump_output==={output}")
    logger.debug(f"script_dump_error==={error}")
    logger.debug(f"script_dump_exit_code==={exit_code}")

    result = libs.run_bash(
        source_connection,
        command=f"/usr/bin/expect -f {file_path}",
        variables=environment_vars,
        use_login_shell=True,
    )

    # strip the each part of result to remove spaces from beginning and
    # last of output
    output = result.stdout.strip()
    error = result.stderr.strip()
    exit_code = result.exit_code

    logger.debug(f"expect_output==={output}")
    logger.debug(f"expect_error==={error}")
    logger.debug(f"expect_exit_code==={exit_code}")

    libs.run_bash(
        source_connection, command=f"rm -rf {file_path}", use_login_shell=True
    )
    if "SHELL_DATA" in environment_vars:
        libs.run_bash(
            source_connection, command="rm -rf $CB_CMD", use_login_shell=True
        )

    if "DLPX_EXPECT_EXIT_CODE" in output:
        exit_code = int(
            output.split("DLPX_EXPECT_EXIT_CODE:")[1].split("\n")[0]
        )
        if "\n" in output:
            msg = (
                output.split("DLPX_EXPECT_EXIT_CODE:")[1]
                .split("\n", 1)[1]
                .strip()
            )
        else:
            msg = ""
        if exit_code != 0:
            error = msg
        else:
            output = msg

    if "cbq>" in output and output.rsplit("\n", 1)[1].strip() == "cbq>":
        output = output.rsplit("\n", 1)[0]

    logger.debug(f"final_output==={output}")
    logger.debug(f"final_error==={error}")
    logger.debug(f"final_exit_code==={exit_code}")
    # Verify the exit code of each executed command. 0 means command ran
    # successfully and for other code it is failed.
    # For failed cases we need to find the scenario in which programs
    # will die and otherwise execution will continue.
    # _handle_exit_code(exit_code, error, output, callback_func)
    return [output, error, exit_code]


def _handle_exit_code(
    exit_code, std_err=None, std_output=None, callback_func=None
):
    if exit_code != 0:
        # Call back function which contains logic to skip the error and
        # continue to throw
        if callback_func:
            logger.debug(
                "Executing call back. Seems some exception is observed. "
                "Validating last error..."
            )
            try:
                result_of_match = callback_func(std_output)
                logger.debug(
                    "Call back result is : {}".format(result_of_match)
                )
                if result_of_match:
                    return True
            except Exception as err:
                logger.debug(
                    "Failed to execute call back function with "
                    "error: {}".format(str(err))
                )

        error_details = std_output
        if error_details is None or error_details == "":
            error_details = std_err
        raise Exception(error_details)
    else:
        return False
