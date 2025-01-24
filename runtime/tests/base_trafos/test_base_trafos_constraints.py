import json

import pytest

from hetdesrun.backend.service.transformation_router import change_code
from hetdesrun.component.code_utils import format_code_with_black
from hetdesrun.trafoutils.io.load import load_transformation_revisions_from_directory
from hetdesrun.utils import State, Type


def test_base_trafos_can_be_loaded_from_dir():
    trafo_dict, _ = load_transformation_revisions_from_directory("./transformations")


def test_base_trafos_only_contain_direct_provisioning_wirings():
    """Base trafos wirings should not contain arbitrary adapter wirings

    Otherwise they are unusable in environments/installations where that adapter is
    not present.

    In particular the frontend execution dialog (hd-wiring) does not handle this
    situation gracefully at the moment.

    Hence we include a test that ensures this.
    """

    trafo_dict, path_dict = load_transformation_revisions_from_directory("./transformations")

    for trafo_id, trafo in trafo_dict.items():
        if trafo.test_wiring is not None:
            for inp_wiring in trafo.test_wiring.input_wirings:
                assert inp_wiring.adapter_id == "direct_provisioning", (
                    f"Found {inp_wiring.adapter_id} as adapter_id in test_wiring input wiring for"
                    f" input {inp_wiring.workflow_input_name} of base trafo "
                    f"{trafo.name} ({trafo.version_tag})"
                    f" with id {trafo_id} from file {path_dict[trafo_id]}."
                )
            for outp_wiring in trafo.test_wiring.output_wirings:
                assert outp_wiring.adapter_id == "direct_provisioning", (
                    f"Found {outp_wiring.adapter_id} as adapter_id in test_wiring output wiring for"
                    f" input {outp_wiring.workflow_output_name} of base trafo "
                    f"{trafo.name} ({trafo.version_tag})"
                    f" with id {trafo_id} from file {path_dict[trafo_id]}."
                )
        if trafo.release_wiring is not None:
            for inp_wiring in trafo.release_wiring.input_wirings:
                assert inp_wiring.adapter_id == "direct_provisioning", (
                    f"Found {inp_wiring.adapter_id} as adapter_id in release_wiring input wiring"
                    f" for input {inp_wiring.workflow_input_name} of base trafo "
                    f"{trafo.name} ({trafo.version_tag})"
                    f" with id {trafo_id} from file {path_dict[trafo_id]}."
                )
            for outp_wiring in trafo.release_wiring.output_wirings:
                assert outp_wiring.adapter_id == "direct_provisioning", (
                    f"Found {outp_wiring.adapter_id} as adapter_id in release_wiring output wiring"
                    f" for input {outp_wiring.workflow_output_name} of base trafo "
                    f"{trafo.name} ({trafo.version_tag})"
                    f" with id {trafo_id} from file {path_dict[trafo_id]}."
                )


def test_base_component_code_agrees_with_json(apply_fixes):
    """Ensure that base component code from .json always agrees with its configuration

    The information contained in the component code via COMPONENT_INFO, the
    main function signature, the included test and release wirings should agree
    with information that is stored directly as part of json files.

    Note: This test can fix the affected components by running pytest with --apply-fixes
    """
    trafo_dict, path_dict = load_transformation_revisions_from_directory("./transformations")

    for trafo_id, trafo in trafo_dict.items():
        if path_dict[trafo_id].endswith(".json") and trafo.type is Type.COMPONENT:
            expanded_updated_code = change_code(
                trafo, expand_component_code=True, update_component_code=True
            )

            if trafo.content != expanded_updated_code and apply_fixes:
                trafo.content = expanded_updated_code

                with open(path_dict[trafo_id], "w", encoding="utf8") as f:
                    json.dump(
                        json.loads(trafo.json(exclude_none=True)),
                        f,
                        indent=2,
                        sort_keys=True,
                    )

            assert trafo.content == expanded_updated_code, (
                f"Component code for base component {trafo.name} ({trafo.version_tag})"
                f" with id {trafo_id} loaded from json file {path_dict[trafo_id]}"
                f" does not agree with expanded(updated(code))."
            )


def test_base_component_code_from_py_is_invariant_under_expanding_and_updating_modulo_formatting(
    apply_fixes,
):
    """Ensure that base component code from .py always agrees with its configuration

    The information contained in the component code via COMPONENT_INFO, the
    main function signature, the included test and release wirings should agree
    with information that is stored directly as part of json files.

    Note: This test can fix the affected components by running pytest with --apply-fixes.
    This however formats them with black, while we use ruff format. Reason is that ruff currently
    offers no (stable) programmatic way to format code strings. So after applying fixes you should
    run the format command (./run format).
    """
    trafo_dict, path_dict = load_transformation_revisions_from_directory("./transformations")

    for trafo_id, trafo in trafo_dict.items():
        if path_dict[trafo_id].endswith(".py") and trafo.type is Type.COMPONENT:
            expanded_updated_code = change_code(
                trafo, expand_component_code=True, update_component_code=True
            )

            black_formatted_trafo_code = format_code_with_black(trafo.content)

            if black_formatted_trafo_code != expanded_updated_code and apply_fixes:
                trafo.content = expanded_updated_code

                with open(path_dict[trafo_id], "w", encoding="utf8") as f:
                    f.write(trafo.content)

            assert black_formatted_trafo_code == expanded_updated_code, (
                f"Black formatted component code for "
                f"base component {trafo.name} ({trafo.version_tag})"
                f" with id {trafo_id} loaded from py file {path_dict[trafo_id]}"
                f" does not agree with expanded(updated(code))."
            )


def test_released_base_trafos_have_a_release_wiring(apply_fixes):
    """All released (and deprecated) trafos should have a release wiring

    Note: This test can fix the affected components by running pytest with --apply-fixes.
    This copies the test wiring to release wiring and updates code of components. For
    components that are kept as .py files this however formats them with black, while we
    use ruff format. Reason is that ruff currently offers no (stable) programmatic way to
    format code strings. So after applying fixes you should run the format
    command (./run format).
    """

    trafo_dict, path_dict = load_transformation_revisions_from_directory("./transformations")

    for trafo_id, trafo in trafo_dict.items():
        if not (trafo.state is State.DRAFT):
            if trafo.release_wiring is None and apply_fixes:
                trafo.release_wiring = trafo.test_wiring

                if trafo.type is Type.COMPONENT:
                    expanded_updated_code = change_code(
                        trafo, expand_component_code=True, update_component_code=True
                    )

                    trafo.content = expanded_updated_code
                    if path_dict[trafo_id].endswith(".py"):
                        with open(path_dict[trafo_id], "w", encoding="utf8") as f:
                            f.write(trafo.content)
                    elif path_dict[trafo_id].endswith(".json"):
                        with open(path_dict[trafo_id], "w", encoding="utf8") as f:
                            json.dump(
                                json.loads(trafo.json(exclude_none=True)),
                                f,
                                indent=2,
                                sort_keys=True,
                            )
                    else:
                        pytest.fail(
                            f"Component path {path_dict[trafo_id]} has wrong file extension!"
                        )
                elif trafo.type is Type.WORKFLOW:
                    assert path_dict[trafo_id].endswith(".json")
                    with open(path_dict[trafo_id], "w", encoding="utf8") as f:
                        json.dump(
                            json.loads(trafo.json(exclude_none=True)),
                            f,
                            indent=2,
                            sort_keys=True,
                        )

            assert trafo.release_wiring is not None, (
                f"Transformation {trafo.name} ({trafo.version_tag})"
                f" with id {trafo_id} loaded from path {path_dict[trafo_id]}"
                f" is released or deprecated but has no release wiring."
            )


def test_base_trafos_have_documentation():
    trafo_dict, path_dict = load_transformation_revisions_from_directory("./transformations")

    for trafo_id, trafo in trafo_dict.items():
        assert trafo.documentation.strip() != "", (
            f"Transformation {trafo.name} ({trafo.version_tag})"
            f" with id {trafo_id} loaded from path {path_dict[trafo_id]}"
            f" has no documentation."
        )
