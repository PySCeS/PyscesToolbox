#!/bin/bash
# Adds instructions for Starting up a PyscesToolbox session
# to the basic_usage.rst file
#

FN=basic_usage.rst
BAKDIR=$(pwd)
cd ../source
TMPFILE=$(tempfile)
cp $FN $TMPFILE
head -n 9 $TMPFILE > $FN
cat basic_usage_additional_text.rst >> $FN
tail -n +10 $TMPFILE >> $FN
rm $TMPFILE
cd $BAKDIR
