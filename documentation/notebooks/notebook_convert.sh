#!/bin/bash
# Converts an IPython/Jupyter Notebook file to reStucturedText2, applies the
# fix_conversion.py python script to the output and copies the file to the
# source directory.
#
file_name_sans_extension=$1

echo "IPython Notebook convesion:"
ipython nbconvert $file_name_sans_extension.ipynb --to rst
echo ""
echo "Fixing conversion:"
python fix_conversion.py $file_name_sans_extension.rst
echo ""
echo "Copying files to source:"
cp -v $file_name_sans_extension.rst ../source/
cp -rv $file_name_sans_extension\_files/ ../source/
