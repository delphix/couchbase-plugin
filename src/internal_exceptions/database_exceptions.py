#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#


from internal_exceptions.base_exceptions import DatabaseException

# Some of below defined exceptions are not being used currently but designed
# for future updates


class DuplicateClusterError(DatabaseException):
    def __init__(self, message=""):
        message = "Duplicate cluster name found, " + message
        super(DuplicateClusterError, self).__init__(
            message,
            "Delete existing staging cluster configuration on source or use "
            "different staging cluster name ",
            "Duplicate cluster names are not allowed",
        )


# When bucket list in snapshot is empty
class FailedToReadBucketDataFromSnapshot(DatabaseException):
    def __init__(self, message=""):
        message = "Please check configurations and try again, " + message
        super(FailedToReadBucketDataFromSnapshot, self).__init__(
            message,
            "Bucket list is empty. Please verify if the bucket exist at "
            "source",
            "bucket list empty",
        )


# Failed To start or stop the server
class CouchbaseServicesError(DatabaseException):
    def __init__(self, message=""):
        message = (
            "Any of start/stop operation for couchbase service fails: "
            + message
        )
        super(CouchbaseServicesError, self).__init__(
            message,
            "Please check the user permission and try again",
            "Not able to stop the couchbase server",
        )


class BucketOperationError(DatabaseException):
    def __init__(self, message=""):
        message = "Bucket operation failed: " + message
        super(BucketOperationError, self).__init__(
            message,
            "Bucket related issue is observed ",
            "Please see logs for more details",
        )
