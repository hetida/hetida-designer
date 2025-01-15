# noqa: INP001
"""Adapter Plugin configuration file of hetida designer Runtime

After the import statements you can insert code to import and register your own
source / sink adapter runtime client implementations for general custom adapters.

See https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/general_custom_adapters/instructions.md

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

from hetdesrun.adapters import (  # noqa: E402
    register_sink_adapter,  # noqa: F401
    register_source_adapter,  # noqa: F401
)

"""
Example:
    from my_package.my_source_adapter import my_source_adapter_load_func
    register_source_adapter("my_adapter_key", my_source_adapter_load_func)

    from my_package.my_sink_adapter import my_sink_adapter_send_func
    register_sink_adapter("my_adapter_key", my_sink_adapter_send_func)
"""

# Registering blob storage adapter
from hetdesrun.adapters.blob_storage.load_blob import (  # noqa: I001, E402
    load_data as blob_storage_load_data,
)
from hetdesrun.adapters.blob_storage.write_blob import (  # noqa: E402
    send_data as blob_storage_send_data,
)

register_source_adapter(adapter_key="blob-storage-adapter", load_func=blob_storage_load_data)

register_sink_adapter(adapter_key="blob-storage-adapter", send_func=blob_storage_send_data)


# Registering local file adapter
from hetdesrun.adapters.local_file import (  # noqa: E402
    load_data as local_file_load_data,
)
from hetdesrun.adapters.local_file import (  # noqa: E402
    send_data as local_file_send_data,
)

register_source_adapter(adapter_key="local-file-adapter", load_func=local_file_load_data)

register_sink_adapter(adapter_key="local-file-adapter", send_func=local_file_send_data)

# Registering sql adapter

from hetdesrun.adapters.sql_adapter import (  # noqa: E402
    load_data as sql_adapter_load_data,
)

register_source_adapter(adapter_key="sql-adapter", load_func=sql_adapter_load_data)

from hetdesrun.adapters.sql_adapter import (  # noqa: E402
    send_data as sql_adapter_send_data,
)

register_sink_adapter(adapter_key="sql-adapter", send_func=sql_adapter_send_data)

# Registering external source adapter

from hetdesrun.adapters.external_sources import load_data as external_source_load_data  # noqa: E402

register_source_adapter(adapter_key="external-sources", load_func=external_source_load_data)

from hetdesrun.adapters.external_sources import send_data as external_source_send_data  # noqa: E402

register_sink_adapter(adapter_key="external-sources", send_func=external_source_send_data)


# Register kafka adapter
from hetdesrun.adapters.kafka import load_data as kafka_adapter_load_data  # noqa: E402

register_source_adapter(adapter_key="kafka", load_func=kafka_adapter_load_data)

from hetdesrun.adapters.kafka import send_data as kafka_adapter_send_data  # noqa: E402

register_sink_adapter(adapter_key="kafka", send_func=kafka_adapter_send_data)


# Registering File Support Handlers for the local file adapter
from hetdesrun.adapters.local_file.extensions import (  # noqa: E402
    FileSupportHandler,
    register_file_support,
)
from hetdesrun.adapters.local_file.handlers.csv import load_csv, write_csv  # noqa: E402

csv_file_support_handler = FileSupportHandler(
    associated_extensions=[
        # this determines which files are associated to the handler functions
        ".csv",
        ".csv.zip",
        ".csv.gz",
        ".csv.bz2",
        ".csv.xz",
    ],
    read_handler_func=load_csv,
    write_handler_func=write_csv,
)

register_file_support(csv_file_support_handler)

from hetdesrun.adapters.local_file.handlers.excel import (  # noqa: E402
    load_excel,
    write_excel,
)

excel_file_support_handler = FileSupportHandler(
    associated_extensions=[
        # this determines which files are associated to the handler functions
        ".xls",
        ".xlsx",
        ".xlsm",
        ".xlsb",
        ".odf",
        ".ods",
        ".odt",
    ],
    read_handler_func=load_excel,
    write_handler_func=write_excel,
)

register_file_support(excel_file_support_handler)

from hetdesrun.adapters.local_file.handlers.hdf import load_hdf, write_hdf  # noqa: E402

hdf_file_support_handler = FileSupportHandler(
    associated_extensions=[
        # this determines which files are associated to the handler functions
        ".h5"
    ],
    read_handler_func=load_hdf,
    write_handler_func=write_hdf,
)

register_file_support(hdf_file_support_handler)

from hetdesrun.adapters.local_file.handlers.parquet import (  # noqa: E402
    load_parquet,
    write_parquet,
)

parquet_file_support_handler = FileSupportHandler(
    associated_extensions=[
        # this determines which files are associated to the handler functions
        ".parquet"
    ],
    read_handler_func=load_parquet,
    write_handler_func=write_parquet,
)

register_file_support(parquet_file_support_handler)


from hetdesrun.adapters.generic_rest.external_types import ExternalType  # noqa: E402
from hetdesrun.adapters.local_file.handlers.pickle import (  # noqa: E402
    load_pickle,
    write_pickle,
)

pickle_filehandler = FileSupportHandler(
    associated_extensions=[
        # this determines which files are associated to the handler functions
        ".pkl"
    ],
    read_handler_func=load_pickle,
    write_handler_func=write_pickle,
    adapter_data_type=ExternalType.METADATA_ANY,
)

register_file_support(pickle_filehandler)
