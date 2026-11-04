"""Test and release wirings of the base transformations

Every base component and workflow should be executable directly from the user interface: Its test
wiring wires all inputs, optional ones with their default value, and executes successfully. Its
release wiring is the same wiring, as if it had been released from the user interface.

Executing all base transformations takes about 20 s, so it only runs with --execute-base-trafos
(or --extended, e.g. via ./run test --extended).
"""

import json
import warnings
from uuid import UUID

import pytest
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from hetdesrun.datatypes import DataType
from hetdesrun.exportimport.importing import import_transformations_from_dir
from hetdesrun.persistence.models.io import InputType
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import load_transformation_revisions_from_directory
from hetdesrun.utils import State

# Base transformations which cannot be wired by manual input, by id
NOT_WIRED: dict[UUID, str] = {
    UUID(trafo_id): reason
    for trafo_id, reason in {
        # Wrap Keras Model with Custom Classes
        "5576783d-421e-475b-bec8-5f2e6535c244": "inputs are a Keras model and classes",
        # Create ExampleClass Object
        "81142909-2bd5-43ea-ba35-de5068a5f8d8": "input is a class",
        # Get ExampleClass Object Attributes (component)
        "47880b66-dbad-4c89-98c9-d39dd13163dd": "input is an object",
        # Get ExampleClass Object Attributes (workflow)
        "ef8a1989-434a-4227-8b4a-cb96635c5a44": "input is an object",
        # Test Keras Model
        "0c4f85b7-1cf1-48be-8cfb-19f228c1f88e": "input is a trained model",
        # Train Keras Model with Custom Layer
        "66fad534-24b0-4188-a4ad-62429497d8f1": "input is a Keras layer class",
        # Load Keras Model with Custom Layer (workflow)
        "2bae9b14-2bd2-4994-9509-9ab46e24838b": "input is a trained model",
        # Decision Function Sklearn Trained Model
        "f35c4918-0a5d-d29c-f3fa-6cfcd425b0f7": "input is a trained model",
        # Predict Sklearn Trained Model
        "41e8bf16-0a16-6021-33c9-88c2f8336df8": "input is a trained model",
        # Show image frame
        "5424ca9d-c892-4469-9340-223f83249f75": "input is an image array",
        # Camera Frame
        "1c78ae7f-0407-4ff3-a9fa-bab1e1b689db": "requires a camera",
        # Get R Dataset
        "80f4f916-4568-29bb-3f94-b487b0612232": "requires internet access",
        # Load Object
        "eb8e8d6b-ba7d-dc88-14dc-6839a471d5e0": "requires a stored object",
        # Store Object 1.0.0
        "26d99461-38a9-5e92-df4f-d0fd2752879e": "writes into the model repository",
        # Store Object 1.0.1
        "d65c8f5d-e714-4581-968d-32d97754f31f": "writes into the model repository",
        # Markdown File
        "c7fc3132-459c-4ede-8b06-59974b50eb17": "writes a file",
    }.items()
}

# Wired base transformations which cannot be executed in the tests, by id
NOT_EXECUTED: dict[UUID, str] = {
    UUID(trafo_id): reason
    for trafo_id, reason in {
        # AntirectifierLayer
        "b871f417-a28a-420a-8a5f-752a31d613db": "requires tensorflow",
        # Persist Wrapped Keras Model with Custom Layer (workflow)
        "0023ea79-9f85-4806-8dfd-d45d6ecd7510": "requires tensorflow",
        # Hetida Platform Assets 0.1.5 and 0.1.6
        "73f4078c-7672-471a-b852-98a35df7bb3b": "requires a hetida platform",
        "16fb6548-f620-4c76-9e7a-e2c1f72ca300": "requires a hetida platform",
        # Hetida Platform Channel Timeseries Data 0.1.8 and 0.1.9
        "15f06de7-472a-4429-b558-20b98f9cd0c9": "requires a hetida platform",
        "c6378f34-6038-4127-b829-19bcd9bd405b": "requires a hetida platform",
        # Hetida Platform Signal Timeseries Data 0.1.11 and 0.1.12
        "0adf6cff-b7ea-4fb5-aea9-43c41cafe415": "requires a hetida platform",
        "329b1f21-b8aa-4c80-bb5f-8fa1dcae75ef": "requires a hetida platform",
        # Load Pegelonline Timeseries
        "230dfa9a-0efe-4418-a5b4-2ac3954ebd8f": "requires internet access",
    }.items()
}

# Warnings expected when executing base transformations with their test wiring, by id
EXPECTED_WARNINGS: dict[UUID, list[tuple[type[Warning], str]]] = {
    # Simple Scatter Map Plot 1.0.0, deprecated in favor of 1.0.1 using scatter_map
    UUID("dc909fa2-93fa-3205-e31d-b05f944cbd29"): [
        (DeprecationWarning, r"\*scatter_?mapbox\* is deprecated")
    ],
    # Exponential Smoothing 1.0.0 and 1.0.1: fitting the model to the test data does not
    # converge for some parameters tried by the hyperparameter search
    UUID("61ef085b-0a83-443b-a4ee-dc1cc6ce1077"): [
        (ConvergenceWarning, "Optimization failed to converge")
    ],
    UUID("8c5f6a7e-2b1d-4f6c-9d9e-c7e3b4a2c1d0"): [
        (ConvergenceWarning, "Optimization failed to converge")
    ],
}

BASE_TRAFOS, BASE_TRAFO_PATHS = load_transformation_revisions_from_directory("./transformations")


def default_value_str(default_value: str | None) -> str:
    """The filter value of an input wiring using the default value"""
    return "null" if default_value is None else default_value


def wiring_issues(tr: TransformationRevision) -> list[str]:
    inputs_by_name = {inp.name: inp for inp in tr.io_interface.inputs}
    input_wirings_by_name = {iw.workflow_input_name: iw for iw in tr.test_wiring.input_wirings}

    issues = [
        f"wiring of unknown input {name}"
        for name in input_wirings_by_name.keys() - inputs_by_name.keys()
    ] + [
        f"wiring of unknown output {ow.workflow_output_name}"
        for ow in tr.test_wiring.output_wirings
        if ow.workflow_output_name not in {outp.name for outp in tr.io_interface.outputs}
    ]

    if tr.id in NOT_WIRED:
        if len(input_wirings_by_name) != 0:
            issues.append("wired, but listed in NOT_WIRED")
    else:
        issues += [
            f"input {name} not wired"
            for name in inputs_by_name.keys() - input_wirings_by_name.keys()
        ]

    for name, iw in input_wirings_by_name.items():
        if name not in inputs_by_name or iw.adapter_id != "direct_provisioning":
            continue
        inp = inputs_by_name[name]
        value = iw.filters.get("value")
        if iw.use_default_value:
            if inp.type is not InputType.OPTIONAL:
                issues.append(f"required input {name} uses default value")
            elif inp.data_type is not DataType.Boolean and value != default_value_str(inp.value):
                issues.append(
                    f"input {name} uses default value {inp.value!r}, but its value is {value!r}"
                )
        elif inp.data_type is DataType.Boolean and value not in ("True", "False"):
            # the user interface only accepts these
            issues.append(f"boolean input {name} has value {value!r} instead of True or False")

    if tr.state is State.DRAFT:
        if tr.release_wiring is not None:
            issues.append("draft with release wiring")
    elif tr.release_wiring != tr.test_wiring:
        issues.append("release wiring differs from test wiring")

    return issues


def test_wirings_of_base_trafos_are_complete():
    issues = {
        BASE_TRAFO_PATHS[tr.id]: tr_issues
        for tr in BASE_TRAFOS.values()
        if len(tr_issues := wiring_issues(tr)) != 0
    }
    assert issues == {}

    assert NOT_WIRED.keys() <= BASE_TRAFOS.keys()
    assert NOT_EXECUTED.keys() <= BASE_TRAFOS.keys()
    assert EXPECTED_WARNINGS.keys() <= BASE_TRAFOS.keys()


@pytest.mark.base_trafo_execution
@pytest.mark.asyncio
async def test_base_trafos_execute_with_their_test_wiring(
    mocked_clean_test_db_session, async_test_client
):
    import_transformations_from_dir("./transformations", directly_into_db=True)

    failures = {}
    async with async_test_client as ac:
        for tr in BASE_TRAFOS.values():
            if tr.id in NOT_WIRED or tr.id in NOT_EXECUTED:
                continue
            with warnings.catch_warnings():
                for category, message in EXPECTED_WARNINGS.get(tr.id, []):
                    warnings.filterwarnings("ignore", message, category)
                # like the user interface, which sends the test wiring
                resp = await ac.post(
                    "/api/transformations/execute",
                    json={
                        "id": str(tr.id),
                        "wiring": json.loads(tr.test_wiring.model_dump_json()),
                        "run_pure_plot_operators": True,
                    },
                )
            if resp.status_code != 200:
                failures[BASE_TRAFO_PATHS[tr.id]] = f"status {resp.status_code}: {resp.text}"
            elif (error := resp.json()["error"]) is not None:
                failures[BASE_TRAFO_PATHS[tr.id]] = f"{error['type']}: {error['message']}"

    assert failures == {}, "\n".join(
        f"{path}: {message[:500]}" for path, message in sorted(failures.items())
    )
