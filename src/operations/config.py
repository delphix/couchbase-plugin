#
# Copyright (c) 2020-2023 by Delphix. All rights reserved.
#

##############################################################################
"""
This file contains global variables. There are some cases when we need to pass
the parameters from one module to another without using the function, then use
global variables. We should try to avoid this approach.
Although in some cases this approach saves a good number of code lines.
We should use this file only for that purpose
"""
##############################################################################


SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = True
SNAP_SYNC_FLAG_TO_USE_CLEANUP_ONLY_IF_CURRENT_JOB_CREATED = True
XDCR_SYNC_FILE_NAME = ""
CBBKP_SYNC_FILE_NAME = ""
SNAP_SYNC_FILE_NAME = ""
SYNC_FILE_NAME = ""
