#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

# This is interface which must be included by all child class of Resource.
# This is child class of Resource and parent class of CouchbaseOperation
# Therefore child class has to implement the method generate_environment_map
# Mixin class(Class which is implementing this interface) created only in
# two cases:
#   1-> Bunch of methods belonging to one group
#   2-> Environment data is common for all the commands
# For case #1, it's about practice we should follow in software development
# For case #2, if such kind of cases are there in which common env data is
# required in execution of multiple commands
# then we club them in one class. Implement 'generate_environment_map' method
# and let it used by all methods defined in
# class.
# Other benefits are: Can call read_map to read each env data, Handling of
# attribute error while generating the env data


import logging

logger = logging.getLogger(__name__)


class MixinInterface(object):
    def generate_environment_map(self):
        raise Exception("You need to implement this method in child class")

    @staticmethod
    def read_map(env):
        logger.debug([(key, env[key]) for key in env])

    @staticmethod
    def check_attribute_error(function):
        def inner(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except AttributeError as AE:
                logger.debug(
                    "Failed to read value from schema objects. "
                    "Error: {}".format(str(AE))
                )
                raise

        return inner
