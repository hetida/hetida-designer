# Highpass Filter

## Description
This component is a digital first-order highpass-filter.

## Inputs
* **data** (Pandas Series): The indices must be datetimes with constant differences, the values must be numeric.
* **frequency** (Float): Cut-off frequency. 

## Outputs
* **filtered** (Pandas Series): The filtered data.

## Details
The component filters a Pandas Series with a given cut-off frequency. The result is a Pandas Series, containing only frequencies greater than the cut-off frequency.
