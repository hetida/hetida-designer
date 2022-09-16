# DataFrames and Series with attached Metadata

Both [pandas DataFrames](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html) and [pandas Series](https://pandas.pydata.org/pandas-docs/version/1.0.0/reference/api/pandas.Series.attrs.html) can have metadata attached in their attribute `attrs`.

The hetida designer [adapter system](./adapter_system/generic_rest_adapters/web_service_interface.md) supports this.

To extract or update the metadata the corresponding base components "Extract Attributes (DataFrame)", "Extract Attributes (Series)", "Add/Update Attributes (DataFrame)", and "Add/Update Attributes (Series)" are available in the category "Connectors".

<img src="./assets/metadata_base_components.png" height="110" width=850> 

**Note:** Neither the local file adapter nor the default adapter "direct_provisioning" (`manual input`, `Only Output`) supports sending or receiving of metadata in `attrs`.

The "Extract Attributes" components reads `attrs` from the Dataframe/Series object and outputs it as a Python dictionary.

The "Add/Update Attributes" components update the metadata dictionary stored in `attrs` of the Dataframe/Series.

These components are quite useful for testing components or workflows which expect Series or DataFrames with metadata.

<img src="./assets/add_metadata_for_test.png" height="110" width=850> 
