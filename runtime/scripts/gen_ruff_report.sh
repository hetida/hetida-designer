#!/usr/bin/env bash

echo "CALLING RUFF"
python3 -m ruff --output-format junit hetdesrun tests >ruff_report.xml

echo "FINISH RUFF"
exit 0 # ruff may throw exit code != 0 if it finds something!
