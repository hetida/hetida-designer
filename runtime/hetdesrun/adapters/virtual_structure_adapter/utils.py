from hetdesrun.models.wiring import InputWiring


def get_actual_sources_and_sinks_for_virtual_sources_and_sinks(
    ref_id_list: list[str],
) -> dict[str, InputWiring]:
    actual_inputs_dict = {}
    for ref_id in ref_id_list:
        actual_source = InputWiring(  # noqa: Q003
            workflow_input_name="dummy",
            adapter_id="direct_provisioning",
            filters={"value": '{"nf": {"b" : 23}}'},  # noqa: Q003
        )
        actual_inputs_dict[ref_id] = actual_source
    return actual_inputs_dict
