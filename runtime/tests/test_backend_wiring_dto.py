from hetdesrun.backend.models.wiring import WiringFrontendDto

valid_wiring_dto_dict = {
    "id": "e4c36380-4b4d-4c97-b3f2-c8c25d25e5c8",
    "name": "STANDARD-WIRING",
    "inputWirings": [
        {
            "id": "e5ed757f-f8b0-45f0-be68-e00b0d0184a9",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowInputName": "inp_series",
            "adapterId": "direct_provisioning",
            "filters": {"value": '{"2020-05-01T00:00:00.000Z":2.5340945967}'},
            "value": None,
        },
        {
            "id": "b29eb7b7-eae9-4711-b245-cd555456b9d0",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowInputName": "limit",
            "adapterId": "direct_provisioning",
            "filters": {"value": "1.3"},
            "value": None,
        },
        {
            "id": "4454bb31-21e1-4a33-9555-6d919d6be9fd",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowInputName": "num_days_forecast",
            "adapterId": "direct_provisioning",
            "filters": {"value": "30"},
            "value": None,
        },
    ],
    "outputWirings": [
        {
            "id": "9658ae49-ec4d-4a0c-bed1-d28c6de7814f",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowOutputName": "intercept",
            "adapterId": "direct_provisioning",
        },
        {
            "id": "c585607e-b8e0-445a-8b78-633c6875c8dd",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowOutputName": "slope",
            "adapterId": "direct_provisioning",
        },
        {
            "id": "d40fb12d-67f0-415f-887c-9e9aa3cbfad3",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowOutputName": "rul_regression_result_plot",
            "adapterId": "direct_provisioning",
        },
        {
            "id": "5ce41007-cc70-4639-b022-6bd54e7152fd",
            "refId": None,
            "refIdType": None,
            "refKey": None,
            "type": None,
            "workflowOutputName": "limit_violationTimestamp",
            "adapterId": "direct_provisioning",
        },
    ],
}


def test_wiring_validators_accept_valid_wiring():
    WiringFrontendDto(**valid_wiring_dto_dict)


def test_to_wiring_from_wiring_match():
    wiring_dto = WiringFrontendDto(**valid_wiring_dto_dict)
    wiring = wiring_dto.to_wiring()
    obtained_wiring_dto = WiringFrontendDto.from_wiring(wiring, wiring_dto.id)

    assert wiring_dto.name == obtained_wiring_dto.name
    assert len(wiring_dto.input_wirings) == len(obtained_wiring_dto.input_wirings)
    for index in range(len(wiring_dto.input_wirings)):
        assert (
            wiring_dto.input_wirings[index].workflow_input_name
            == obtained_wiring_dto.input_wirings[index].workflow_input_name
        )
    assert len(wiring_dto.output_wirings) == len(obtained_wiring_dto.output_wirings)
    for index in range(len(wiring_dto.output_wirings)):
        assert (
            wiring_dto.output_wirings[index].workflow_output_name
            == obtained_wiring_dto.output_wirings[index].workflow_output_name
        )
