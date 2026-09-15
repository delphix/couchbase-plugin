#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

import logging
import re
import sys
import traceback
import types

from db_commands.constants import ALREADY_CLUSTER_FOR_BUCKET
from db_commands.constants import ALREADY_CLUSTER_INIT
from db_commands.constants import BUCKET_NAME_ALREADY_EXIST
from db_commands.constants import CLUSTER_ALREADY_PRESENT
from db_commands.constants import MULTIPLE_VDB_ERROR
from db_commands.constants import SHUTDOWN_FAILED
from dlpx.virtualization.platform.exceptions import UserError
from internal_exceptions.base_exceptions import GenericUserError
from internal_exceptions.plugin_exceptions import ERR_RESPONSE_DATA

logger = logging.getLogger(__name__)


# This is meta class which  decorates the each functions of child
# class with below things:
# Ignore common exceptions
# Enable logging in more intuitive way


class DatabaseExceptionHandlerMeta(type):
    def __new__(mcs, caller_name, caller_base_name, attr_in_caller):
        """
        :param caller_name:
        :type caller_name: Class type
        :param caller_base_name:
        :type caller_base_name: Any base class of caller_name
        :param attributes_in_caller:
        :type attributes_in_caller: functions and parameters of class
        :return:
        """

        # iteration for each method of a caller class
        for attribute_name, attribute_value in attr_in_caller.iteritems():
            if isinstance(attribute_value, types.FunctionType):
                if (
                    attribute_name == "__init__"
                    or attribute_name == "status"
                    or attribute_name == "check_attribute_error"
                ):
                    continue
                a = mcs.handle_exception_decorator(attribute_value)
                attr_in_caller[attribute_name] = a
        try:
            return super(DatabaseExceptionHandlerMeta, mcs).__new__(
                mcs, caller_name, caller_base_name, attr_in_caller
            )
        except Exception as err:
            logger.debug(
                "Exception occurred in metaclass: {}".format(
                    str(err),
                )
            )
            raise

    @classmethod
    def _exception_generator_factory(mcs, err_string):
        """
        :param err_string:
        :raises: Exceptions based on the output. It matches the error string
        with predefined strings.
               In some cases we need to kill the program and in some cases it
               is not. This is distinguished by the
               error string.
        """
        if (
            re.search(CLUSTER_ALREADY_PRESENT, err_string)
            or re.search(BUCKET_NAME_ALREADY_EXIST, err_string)
            or re.search(MULTIPLE_VDB_ERROR, err_string)
            or re.search(SHUTDOWN_FAILED, err_string)
            or re.search(ALREADY_CLUSTER_FOR_BUCKET, err_string)
            or re.search(ALREADY_CLUSTER_INIT, err_string)
        ):
            logger.debug("Gracefully accepted the last exception")
            return
        logger.debug("Searching predefined exception for this error")
        err_code = get_err_code(err_string)
        raise GenericUserError(
            ERR_RESPONSE_DATA[err_code]["MESSAGE"],
            ERR_RESPONSE_DATA[err_code]["ACTION"],
            err_string,
        )

    @classmethod
    def handle_exception_decorator(mcs, function_name):
        """
        Decorating function with exception handling. Also we can control the
        output of each couchbase
        command at single place.
        :param function_name: Method of a class which is not static and class
        :type : function
        :return : None
        """

        def wrapper_function(*args, **kwargs):
            try:
                output_list = function_name(*args, **kwargs)
                return output_list

            except UserError:
                logger.debug("User Error found")
                ttype, value, traceb = sys.exc_info()
                logger.debug("type: {}, value: {}".format(ttype, value))
                logger.debug("trackback")
                logger.debug(traceback.format_exc())
                raise

            except Exception as error:
                logger.debug("Caught Exception : {}".format(str(error)))
                logger.debug("pioro")
                ttype, value, traceb = sys.exc_info()
                logger.debug("type: {}, value: {}".format(ttype, value))
                logger.debug("trackback")
                logger.debug(traceback.format_exc())
                mcs._exception_generator_factory(str(error))

        return wrapper_function


# Return error code for given string if it is defined in RESPONSE_DATA
def get_err_code(error_string):
    logger.debug("error_string is {}".format(error_string))
    all_error_codes = ERR_RESPONSE_DATA.keys()
    for each_err_code in all_error_codes:
        search_string = ERR_RESPONSE_DATA[each_err_code]["ERR_STRING"]
        if re.search(search_string, error_string):
            return each_err_code
    return "DEFAULT_ERR"
