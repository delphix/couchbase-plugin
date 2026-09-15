#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
"""
There are two purposes which this module is created for:
Purpose1:
 This class is being used by child classes to initialize their attributes.
 Child classes of this are :
 _bucket.py,_cb_backup.py, _cluster.py, _replication.py, _xdcr.py. To add any
 new feature let say 'X', create a class
 for that 'X' feature in x module and make the Resource class as parent for X.
 Here we are using builder design pattern to initialize the properties.
 Reason of using this approach:
 1: No need fixed combinations of objects.
 There could be multiple attributes combinations based on their availability.
 Possible combinations are like objects of
 ('repository' + 'virtual_source' )or (' repository' +'staged_source').
 Instead of creating multiple constructors,
  followed this approach in which whatever the parameters available to object
  creator, pass only those.
 Remaining class attributes will be set as 'None'.
 To create object use below format, type of obj is Resource.
 `Example`:
 obj=Resource.ObjectBuilder().set_snapshot_parameters("SnapshotParams").
 set_snapshot("Snapshot").set_dsource(False).build()
 Also we must end the object creation with build(), after which only
 ObjectBuilder will get to know about no more
 attributes to set.
 2: No need to remember which constructor should be called for any particular
 purpose
 3: No need to remember the order of parameters
 4: If you want to add other parameters in this class, refactoring will be
 easier in this approach

Part2:
 __metaclass__ of this class is DatabaseExceptionHandlerMeta. All child classes
  of Resource will automatically
 inherit this property. Child classes will be decorated with small features for
  now, which we can scale.
 Current usage: more readable logs and handling of ignorable exceptions.
 Basically there is a decorator(inside metaclass) which is being applied on all
  methods defined inside the child class.
 Through this design, no need to write decorators on top of each function
 manually.
"""
##############################################################################

import logging

from controller.db_exception_handler import DatabaseExceptionHandlerMeta

logger = logging.getLogger(__name__)


class Resource(object):
    __metaclass__ = DatabaseExceptionHandlerMeta

    def __init__(self, builder):
        """
        It requires the builder object to initialize the parameters of this
        class.
        builder is object of inner class: ObjectBuilder
        :param builder:
        :return Object of Resource
        """
        # Validating the type of builder. It must be of two type
        # (type or Resource). Else it will raise an Exception for
        # other cases like string, int or object of any other class.
        if (
            isinstance(builder, type)
            or isinstance(builder, Resource)
            or builder.__class__.__name__ == "Resource"
        ):
            self.connection = builder.connection
            self.repository = builder.repository
            self.source_config = builder.source_config
            self.snapshot_parameters = builder.snapshot_parameters
            self.staged_source = builder.staged_source
            self.virtual_source = builder.virtual_source
            self.snapshot = builder.snapshot
            self.dSource = builder.dSource
            self.parameters = builder.parameters
        else:
            logger.debug(
                "Error, Expected builder object, Found: {} ".format(
                    type(builder)
                )
            )
            raise Exception(
                "Failed to initialize the Resource object. Expected: "
                "ObjectBuilder, Found: {} ".format(type(builder))
            )

    class ObjectBuilder(object):
        # Below are the same parameters which is required in Resource class
        # All setters must be decorated with classmethod, because there will
        # not be any instance of ObjectBuilder
        connection = None
        repository = None
        source_config = None
        snapshot_parameters = None
        staged_source = None
        virtual_source = None
        snapshot = None
        dSource = None
        parameters = None

        @classmethod
        def set_connection(cls, rx_connection):
            cls.connection = rx_connection
            return cls

        @classmethod
        def set_repository(cls, repo):
            cls.repository = repo
            return cls

        @classmethod
        def set_source_config(cls, config):
            cls.source_config = config
            return cls

        @classmethod
        def set_snapshot_parameters(cls, snapshot_params):
            cls.snapshot_parameters = snapshot_params
            return cls

        @classmethod
        def set_staged_source(cls, source_obj):
            cls.staged_source = source_obj
            cls.connection = source_obj.staged_connection
            cls.parameters = source_obj.parameters
            cls.dSource = True
            return cls

        @classmethod
        def set_virtual_source(cls, source_obj):
            cls.virtual_source = source_obj
            cls.connection = source_obj.connection
            cls.parameters = source_obj.parameters
            cls.dSource = False
            return cls

        @classmethod
        def set_snapshot(cls, snapshot_data):
            cls.snapshot = snapshot_data
            return cls

        @classmethod
        def set_dsource(cls, is_dSource=True):
            if is_dSource is None:
                raise Exception("Dataset object cannot be None")
            cls.dSource = is_dSource
            return cls

        # it must be last step in order to provide the outer class
        # object(Resource)
        @classmethod
        def build(cls):
            if cls.dSource is None:
                raise Exception(
                    "If this object is for dSource then set True else set "
                    "it False"
                )
            return Resource(cls)

    def __repr__(self):
        """
        overriding the __repr__ method. To print contents of Resource object,
        use print(obj)
        :return:None
        """
        return (
            "\nObjectBuilder(connection: {0.connection!r}, repository: "
            "{0.repository!r}, \n source_config: {0.source_config!r}, "
            "snapshot_parameters:{0.snapshot_parameters!r},\
                staged_source: {0.staged_source!r}, "
            "virtual_source:{0.virtual_source!r}, snapshot: "
            "{0.snapshot!r}, parameters:{0.parameters!r},dSource: "
            "{0.dSource!r})".format(self)
        )

    def __str__(self):
        return repr(self)
