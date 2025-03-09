#!/bin/sh
# This script will convert files with ":" in their name to "|"
# when you save web pages mac uses ":" in the file name, which is not supported in windows

find . -depth -name "*:*" -exec sh -c '
  f="$1"
  newname=$(echo "$f" | tr ":" "|")
  [ "$f" != "$newname" ] && mv -- "$f" "$newname"
' sh {} \;