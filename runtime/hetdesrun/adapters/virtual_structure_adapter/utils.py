from hetdesrun.models.wiring import InputWiring


def get_actual_sources_and_sinks_for_virtual_sources_and_sinks(
    ref_id_list: list[str],
) -> dict[str, InputWiring]:
    actual_source = InputWiring(  # noqa: Q003
        workflow_input_name="dummy",
        adapter_id="direct_provisioning",
        filters={"value": '{"nf": {"b" : 23}}'},  # noqa: Q003
    )
    return {ref_id_list[0]: actual_source}
