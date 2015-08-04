#!/bin/bash

pythonenv=".python-env"
if [ ! -d '$pythonenv' ]; then
    virtualenv $pythonenv
else
    echo "Virtual environment already exists ($pythonenv)"
fi

echo "Enable virtual environment with 'source ./$pythonenv/bin/activate'"
