import json
import os
from copy import deepcopy
from datetime import datetime, timedelta
from unittest import mock
from uuid import uuid4

from hetdesrun.exportimport.purge import deprecate_all_but_latest_in_group
from hetdesrun.persistence.models.transformation import TransformationRevision


def test_deprecate_all_but_latest_in_group():
    path = os.path.join(
        "tests",
        "data",
        "components",
        "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.json",
    )
    with open(path) as f:
        import_wf_json = json.load(f)
    import_wf = TransformationRevision(**import_wf_json)
    stored_wf_json = deepcopy(import_wf_json)
    stored_wf_json["id"] = str(uuid4())
    stored_wf_json["version_tag"] = "0.1.0"
    stored_wf_json["released_timestamp"] = datetime.isoformat(
        datetime.fromisoformat(import_wf_json["released_timestamp"])
        - timedelta(weeks=1)
    )
    stored_wf = TransformationRevision(**stored_wf_json)
    stored_wf.deprecate()
    deprecated_stored_json = json.loads(stored_wf.json())

    with mock.patch(
        "hetdesrun.exportimport.purge.get_transformation_revisions",
        return_value=[import_wf, stored_wf],
    ) as patched_get:
        with mock.patch(
            "hetdesrun.exportimport.purge.update_or_create_transformation_revision",
            return_value=None,
        ) as patched_update:
            deprecate_all_but_latest_in_group(
                revision_group_id=import_wf.revision_group_id
            )

            assert patched_get.call_count == 1

            assert patched_update.call_count == 1
            _, args, _ = patched_update.mock_calls[0]
            update_tr = args[0]
            update_json = json.loads(update_tr.json())
            del update_json["disabled_timestamp"]
            del deprecated_stored_json["disabled_timestamp"]
            assert update_json == deprecated_stored_json
