export PYTHONPATH=$PYTHONPATH:..
when-changed ../arteria/* ./runfolder_tests.py -c "clear && python runfolder_tests.py"
