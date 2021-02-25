"""Configuration of Hetida Designer Runtime

After the import statements you can insert code to import and register your own
source / sink adapter runtime client implementations.

They must comply with following signatures:

async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: Dict[str, FilteredSource],
    adapter_key: str,
) -> Dict[str, Any]

async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: Dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict,
    adapter_key: str,
) -> Dict[str, Any]

Notes:
* You can provide both functions or coroutine functions (Awaitables)
* The types returned by a loading function must comply with the the hetida designer data types.
  For example the adapter may return pandas Series objects (which can be used in SERIES inputs)
* A send data function should return an empty dictionary. The option to return an actual data 
  dictionary exists only to support the built-in direct provisioning adapter.
* FilteredSource and FilteredSink Protocol types can be imported from hetdesrun.models for type
  annotations or you provide your own structurally equivalent type.


This file must be in PYTHONPATH as well as your adapter implementation packages / modules you
are importing here.
"""

from hetdesrun.adapters import register_source_adapter, register_sink_adapter


"""
Example:
    from my_package.my_source_adapter import my_source_adapter_load_func
    register_source_adapter("my_adapter_key", my_source_adapter_load_func)

    from my_package.my_sink_adapter import my_sink_adapter_send_func
    register_sink_adapter("my_adapter_key", my_sink_adapter_send_func)
"""
