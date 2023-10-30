from hetdesrun.persistence.models.link import Link, Vertex

workflow_input_dict = {
    "connector_id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
    "connector_name": "input",
    "data_type": "SERIES",
    "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
    "name": "y_vals",
    "operator_id": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
    "operator_name": "Name Series",
    "position": {"x": -50, "y": 370},
    "type": "REQUIRED",
    "value": None,
}
wf_input_vertex_dict = {
    "connector": {
        "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
        "name": "y_vals",
        "data_type": "SERIES",
        "position": {"x": -50, "y": 370},
    }
}

operator_input_dict = {
    "data_type": "SERIES",
    "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
    "name": "input",
    "type": "OPTIONAL",
    "value": None,
    "position": {"x": 0, "y": 0},
    "exposed": True,
}
op_input_vertex_dict = {
    "operator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
    "connector": {
        "data_type": "SERIES",
        "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
        "name": "input",
        "position": {"x": 0, "y": 0},
    },
}

operator_output_dict = {
    "data_type": "SERIES",
    "id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
    "name": "output",
    "position": {"x": 0, "y": 0},
}
op_output_vertex_dict = {
    "operator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
    "connector": {
        "data_type": "SERIES",
        "id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
        "name": "output",
        "position": {"x": 0, "y": 0},
    },
}

workflow_output_dict = {
    "connector_id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
    "connector_name": "output",
    "data_type": "SERIES",
    "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
    "name": "y_vals",
    "operator_id": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
    "operator_name": "Name Series (2)",
    "position": {"x": 2010, "y": -100},
}
wf_output_vertex_dict = {
    "connector": {
        "data_type": "SERIES",
        "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
        "name": "y_vals",
        "position": {"x": 2010, "y": -100},
    }
}

link_from_wf_input_to_op_input_dict = {
    "start": wf_input_vertex_dict,
    "end": op_input_vertex_dict,
}
link_from_op_output_to_op_input_dict = {
    "start": op_output_vertex_dict,
    "end": op_input_vertex_dict,
}
link_from_op_output_to_wf_output_dict = {
    "start": op_output_vertex_dict,
    "end": wf_output_vertex_dict,
}


def test_valid_vertex_accepted() -> None:
    Vertex(**wf_input_vertex_dict)
    Vertex(**op_input_vertex_dict)
    Vertex(**op_output_vertex_dict)
    Vertex(**wf_output_vertex_dict)


def test_valid_link_accepted() -> None:
    Link(**link_from_wf_input_to_op_input_dict)
    Link(**link_from_op_output_to_op_input_dict)
    Link(**link_from_op_output_to_wf_output_dict)


def test_link_validator_types_match() -> None:
    pass


def test_link_validator_no_self_reference() -> None:
    pass


def test_link_to_workflow_connection() -> None:
    pass
