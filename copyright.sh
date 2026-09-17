#!/bin/bash
#
# Copyright (c) 2022, 2023 by Delphix. All rights reserved.
#

function verify_copyright() {
	file=$1
	current_year=$(date +%Y)
  if [[ $(grep -e "Copyright (c).*$current_year .*Delphix. All rights reserved." "$file") ]] ; then
      return 0
  else
      echo "Copyright check failed for file: $file"
      return 1
 fi

}

code=0
for file in "$@" ; do
	verify_copyright "$file"
	code=$(($? + $code))
done
exit $code
