#!/usr/bin/env bash

echo "CALLING PYLINT"
python3 -m pylint -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" hetdesrun > pylint_report.txt
echo "FINISH PYLINT"
exit 0 # pylint may throw exit code != 0 if it finds something!