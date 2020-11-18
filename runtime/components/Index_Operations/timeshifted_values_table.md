# Timeshifted Value Table

## Description
The component takes a Series and returns a DataFrame of regular time shifted values.

## Inputs
* **timeseries** (Pandas Series): Should be a Pandas Series with a DateTime Index.
* **freq** (String): Frequency String. For example "20d", "m" or "12min".
* **periods** (Integer): Number of times the series is shifted by the **freq**. Can be negative for negative shifts.

## Outputs
* **timeshifted_values** (Pandas DataFrame): The resulting DataFrame containing one column for every shift. NaN Values may occur.

## Details
Shifts the given series **periods** times by the given frequency and gathers all such resulting shifted series into one DataFrame.
