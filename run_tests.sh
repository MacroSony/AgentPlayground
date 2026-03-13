#!/bin/bash
# If we are in github actions, we use system python
if [ -z "$GITHUB_ACTIONS" ]; then
    .venv/bin/python -m pip install -r requirements.txt
    export OPENBLAS_NUM_THREADS=1
    .venv/bin/python -m unittest discover -s tests
else
    python -m pip install -r requirements.txt
    python -m unittest discover -s tests
fi
