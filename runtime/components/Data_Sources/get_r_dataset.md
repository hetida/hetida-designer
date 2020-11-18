# Get R Dataset

## Description
Download an R dataset and obtain it as a DataFrame.

## Inputs
* **dataname** (String): The name of the dataset (e.g. "iris" or "bostonc").
* **tag** (String): The package of the dataset (e.g. "datasets" or "DAAG").

## Outputs
* **data** (Pandas DataFrame): The loaded data set. 

## Details

This needs a working internet connection of the hetida designer runtime. Downloading a dataset may take a moment depending on its size and your connection speed.

**Warning**: Datasets may be re-downloaded with every execution of this component. This component should only be used for one-off demo runs.

This component allows to use classical/example/demo datasets provided by some R packages.

See https://vincentarelbundock.github.io/Rdatasets/datasets.html for a list of available datasets.

This component uses the statsmodels library for downloading the datasets (https://www.statsmodels.org/dev/datasets/statsmodels.datasets.get_rdataset.html).

## Examples
The json input of a typical call of this component to download the classical iris dataset is
```
{
    "dataname": "iris",
    "package": "datasets"
}
```
To get (corrected) Boston housing data use
```
{
    "dataname": "bostonc",
    "package": "DAAG"
}
```
