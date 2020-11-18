"""Configuration of Hetida Designer Runtime

After the import statements you can insert code to import and register your own
source / sink adapter client implementations.

Note: You can provide both functions or coroutine functions (Awaitables)

This file must be in PYTHONPATH as well as your adapter implementation packages / modules.
"""

from hetdesrun.adapters import register_source_adapter, register_sink_adapter

"""
Example:
    from my_package.my_source_adapter import my_source_adapter_load_func
    register_source_adapter("my_adapter_key", my_source_adapter_load_func)

    from my_package.my_sink_adapter import my_sink_adapter_send_func
    register_sink_adapter("my_adapter_key", my_sink_adapter_send_func)
"""
