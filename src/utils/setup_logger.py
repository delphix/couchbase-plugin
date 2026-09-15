#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#


import logging

from dlpx.virtualization import libs


class Logger:
    """ """

    _logger = None

    def __get_mode(self, mode):
        return eval("logging." + mode)

    def __init__(
        self,
        name,
        mode="DEBUG",
        formatter="[%(asctime)s] [%(levelname)-10s] "
        "[%(filename)-15s:%(lineno)2d] %(message)s",
    ):
        if Logger._logger is None:
            vsdkHandler = libs.PlatformHandler()
            vsdkHandler.setLevel(self.__get_mode(mode))
            vsdkFormatter = logging.Formatter(
                formatter,
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            vsdkHandler.setFormatter(vsdkFormatter)
            logger = logging.getLogger(name)
            logger.addHandler(vsdkHandler)
            logger.setLevel(self.__get_mode(mode))
            Logger._logger = logger

    def get_logger(self):
        return Logger._logger


def _setup_logger():
    log_message_format = (
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
    )
    log_message_date_format = "%Y-%m-%d %H:%M:%S"

    # Create a custom formatter. This will help in diagnose the problem.
    formatter = logging.Formatter(
        log_message_format,
        datefmt=log_message_date_format,
    )

    platform_handler = libs.PlatformHandler()
    platform_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(platform_handler)

    # By default the root logger's level is logging.WARNING.
    logger.setLevel(logging.DEBUG)
