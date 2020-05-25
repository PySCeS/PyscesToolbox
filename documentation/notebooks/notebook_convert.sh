#!/bin/bash
# Converts an IPython/Jupyter Notebook file to reStucturedText2, applies the
# fix_conversion.py python script to the output and copies the file to the
# source directory.
#
file_name_sans_extension=$1

echo "IPython Notebook conversion to rst:"
jupyter nbconvert $file_name_sans_extension.ipynb --to rst
echo ""
echo "Fixing conversion:"
python fix_conversion.py $file_name_sans_extension.rst
echo ""
echo "Copying files to source:"
cp -v $file_name_sans_extension.rst ../source/
cp -rv $file_name_sans_extension\_files/ ../source/
echo ""
echo "Cleaning example notebook"
python clean_notebooks.py $file_name_sans_extension.ipynb
echo "Copying example notebook to ~/example_notebooks:"
clean=_clean
cp -v $file_name_sans_extension$clean.ipynb ../../example_notebooks/$file_name_sans_extension.ipynb

if [ "$file_name_sans_extension" == "basic_usage" ]; then
    ./fix_basic_usage.sh
fi
