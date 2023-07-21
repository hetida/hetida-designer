from hetdesrun.component.code import (
    check_parameter_names,
    generate_function_header,
    update_code,
)
from hetdesrun.datatypes import DataType
from hetdesrun.models.code import example_code, example_code_async
from hetdesrun.persistence.models.io import (
    InputType,
    IOInterface,
    TransformationInput,
    TransformationOutput,
)
from hetdesrun.persistence.models.transformation import TransformationRevision


def test_function_header_no_params():
    component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert "main()" in func_header
    assert '"inputs": {' + "}" in func_header  # noqa: ISC003
    assert '"outputs": {' + "}" in func_header  # noqa: ISC003
    assert '"id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565"' in func_header


def test_function_header_multiple_inputs():
    component = TransformationRevision(
        io_interface=IOInterface(
            inputs=[
                TransformationInput(name="x", data_type=DataType.Float),
                TransformationInput(name="okay", data_type=DataType.Boolean),
            ],
            outputs=[TransformationOutput(name="output", data_type=DataType.Float)],
        ),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert "main(*, x, okay)" in func_header
    assert (
        """
    "inputs": {
        "x": {"data_type": "FLOAT"},
        "okay": {"data_type": "BOOLEAN"},
    },
    """
        in func_header
    )
    assert (
        """
    "outputs": {
        "output": {"data_type": "FLOAT"},
    },
    """
        in func_header
    )
    assert '"version_tag": "1.0.0"' in func_header


def test_function_header_optional_inputs():
    component = TransformationRevision(
        io_interface=IOInterface(
            inputs=[
                TransformationInput(
                    name="x",
                    data_type=DataType.Float,
                    type=InputType.OPTIONAL,
                    value=1.2,
                ),
                TransformationInput(
                    name="okay",
                    data_type=DataType.Boolean,
                    type=InputType.OPTIONAL,
                    value=False,
                ),
                TransformationInput(
                    name="neither_nor_ok",
                    data_type=DataType.Boolean,
                    type=InputType.OPTIONAL,
                    value="",
                ),
                TransformationInput(
                    name="text",
                    data_type=DataType.String,
                    type=InputType.OPTIONAL,
                    value="text",
                ),
                TransformationInput(
                    name="no_text",
                    data_type=DataType.String,
                    type=InputType.OPTIONAL,
                    value=None,
                ),
                TransformationInput(
                    name="empty_text",
                    data_type=DataType.String,
                    type=InputType.OPTIONAL,
                    value="",
                ),
                TransformationInput(
                    name="series",
                    data_type=DataType.Series,
                    type=InputType.OPTIONAL,
                    value=(
                        '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": '
                        '18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'
                    ),
                ),
            ],
            outputs=[TransformationOutput(name="output", data_type=DataType.Float)],
        ),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert '"default_value": False' in func_header
    assert '"default_value": None' in func_header
    assert '"default_value": 1.2' in func_header
    assert '"default_value": "text"' in func_header
    assert '"default_value": "None"' not in func_header
    assert (
        'main(*, x=1.2, okay=False, neither_nor_ok=None, text="text", no_text=None, empty_text="", '
        'series={\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,'
        '\n    "2020-01-03T08:20:04.000Z": 25.9\n})'
    ) in func_header


def test_check_parameter_names():
    assert check_parameter_names(["x"])
    assert not check_parameter_names(["1", "x"])


def test_update_code():
    component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="RELEASED",
        type="COMPONENT",
        released_timestamp="2019-12-01T12:00:00+00:00",
        content=example_code,
        test_wiring=[],
    )
    updated_component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.1",
        state="DRAFT",
        type="COMPONENT",
        content=example_code,
        test_wiring=[],
    )
    new_code = update_code(updated_component)
    assert """return {"z": x+y}""" in new_code
    assert "c6eff22c-21c4-43c6-9ae1-b2bdfb944565" in new_code
    assert "1.0.0" not in new_code

    # test input without both start/stop markers
    component.content = ""
    new_code = update_code(component)
    assert "pass" in new_code

    # test input without only stop marker
    component.content = "# ***** DO NOT EDIT LINES BELOW *****"
    new_code = update_code(component)

    # test with async def in function header
    component.content = example_code_async
    new_code = update_code(component)
    assert "async def" in new_code
