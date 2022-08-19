# DataFrames and Series with attached Metadata

Both [pandas DataFrames](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.attrs.html) and [pandas Series](https://pandas.pydata.org/pandas-docs/version/1.0.0/reference/api/pandas.Series.attrs.html) can have metadata attached in their attribute `attrs`.

The hetida designer [adapter system](./adapter_system/generic_rest_adapters/web_service_interface.md) support this.

To extract or update the metadata the corresponding base components "Extract Attributes (DataFrame)", "Extract Attributes (Series)", "Add/Update Attributes (DataFrame)", and "Add/Update Attributes (Series)" are available in the category "Connectors".

<img src="./assets/metadata_base_components.png" height="110" width=850> 

**Note:** Neither the local file adapter nor the default adapter "direct_provisioning" (`manual input`, `Only Output`) supports sending or receiving of metadata in `attrs`.

The "Extract Attributes" components provide direct (read) access to what is stored in `attrs`, so that it e.g. can be wired to the default adapter and be displayed in the frontend.
Depending on whether the key-value pair already exist, the "Add/Update Attributes" components add further values or update existing ones, so that metadata can be stored in `attrs` using the default adapter in the dialog.
These components are quite useful for testing components or workflows which expect Series or DataFrames with metadata.

<img src="./assets/add_metadata_for_test.png" height="110" width=850> 
