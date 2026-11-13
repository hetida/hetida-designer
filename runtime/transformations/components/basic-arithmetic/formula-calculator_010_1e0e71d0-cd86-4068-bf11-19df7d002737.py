"""Documentation for Formula Calculator

# Formula Calculator

## Description
Calculates a formula with up to five timeseries, similar to a formula in Excel.

Connect the timeseries you need to the inputs **a**, **b**, **c**, **d** and **e** and write a
formula with these letters, e.g. `(a + b) / 2` for the mean of a and b. The formula is calculated
separately for each point in time: The result at 10:00 is calculated from the values of a and b
at 10:00, the result at 10:15 from the values at 10:15, and so on.

Methods of the timeseries can be used as well, e.g. `a - a.mean()` for the deviation of a from its
mean, `a.rolling("1h").mean()` for the moving average of the last hour or `abcde.std(axis=1)` for
the standard deviation of all connected timeseries at each point in time.

The metadata of the timeseries, like the properties of their signals, can be used as well, e.g.
`a > meta.a.max` for the points in time at which a is larger than its property max.

There is also a German version of this component: "Formelrechner".

## Inputs
* **a**, **b**, **c**, **d**, **e** (SERIES, optional): The timeseries used in the formula. Only
  connect the ones you need.
* **formula** (STRING): The formula, e.g. `(a + b) / 2`.
* **time_zone_from_metadata** (BOOLEAN, optional, default True): Calculates the formula in the
  time zone of the metadata of the timeseries, e.g. for days from midnight to midnight in German
  time, see the examples for time zones. Switch it off with False to calculate the formula in the
  time zones the timeseries have, usually UTC.

## Outputs
* **result** (SERIES): The result of the formula for each point in time.

## How to write a formula
Write formulas like in Excel or on a calculator:
* `+` plus, `-` minus, `*` times, `/` divided by
* `**` to the power of, e.g. `a**2` for a squared (in Excel: `^`)
* `( )` brackets, which are calculated first, e.g. `(a + b) * 2`. Without brackets, powers are
  calculated first, then times and divided by, then plus and minus. So `a + b * 2` is a plus
  twice b.
* Numbers with a point as decimal separator, e.g. `1.5`. Very large and very small numbers can
  be written like `2.5e6` for 2.5 million (2.5 times 10 to the power of 6) and `3e-3` for 0.003.
* `pi` for the number π = 3.14159...
* Functions in lowercase letters followed by brackets, e.g. `sqrt(a)` for the square root of a.
* Methods of a timeseries after a point, e.g. `a.mean()` for the mean of all values of a or
  `a.round(2)` for a rounded to 2 decimal places. All methods are listed in the
  [pandas documentation of Series](https://pandas.pydata.org/docs/reference/series.html).
* `abcde` for a table with all connected timeseries as columns, e.g. `abcde.max(axis=1)` for the
  largest value of all connected timeseries at each point in time.
* `meta` for the metadata of the connected timeseries, e.g. `meta.a.max` for the field max of the
  metadata of a, see the examples for metadata below.
* `modify_timezone(a, "Europe/Berlin")` for a with its points in time in German time, e.g. for
  days from midnight to midnight in German time if a has no metadata, see the examples for time
  zones below.
* `pd`, `np` and `hdhelpers` for the Python libraries pandas, numpy and hdhelpers, e.g.
  `pd.Grouper(freq="D")`, `np.sign(a)` or `hdhelpers.metadata.get_series_info(a, "max")`.
* Text in quotes, e.g. durations like `"1h"` for one hour in `a.rolling("1h").mean()`.

Spaces do not matter: `a+b` is the same as `a + b`. But uppercase and lowercase letters matter:
Write `a` and `sqrt`, not `A` and `SQRT`.

## Differences to Excel
* The inputs a, b, c, d, e take the place of cells like A1 or B2.
* The formula does not need to start with `=` (but it may).
* Powers: `a**2` instead of `a^2`.
* Percent: `a * 19 / 100` or `a * 0.19` instead of `a * 19%`. The sign `%` is the remainder of
  a division here, e.g. `a % 60` (Excel: MOD(a, 60)).
* Comparisons: `==` for equal and `!=` for not equal instead of `=` and `<>`.
* Empty cells count as 0 in Excel. Here, a missing value stays missing: `a + b` has no value
  where a value of a or b is missing. To count missing values as 0, write
  `a.add(b, fill_value=0)` instead of `a + b`, see the examples for missing values below.
* Logarithms: `log` is the natural logarithm (Excel: LN). The logarithm to base 10 is `log10`
  (Excel: LOG).
* Angle of a point: `arctan2(b, a)` is Excel's ATAN2(a, b), with a and b swapped.
* Functions like SUM, AVERAGE, MAX, MIN, ROUND and IF are written differently, e.g.
  `abcde.sum(axis=1)`, `abcde.mean(axis=1)`, `a.round(2)` or `a.where(c > 0, b)`, see the
  examples below.

## Examples
For the timeseries
* a: 10 at 00:00, 20 at 01:00 and 30 at 02:00
* b: 30 at 00:00, 50 at 01:00 and 40 at 02:00

the formula `(a + b) / 2` results in 20 at 00:00, 35 at 01:00 and 35 at 02:00.

The following examples are complete formulas, which you can copy.

### Basic arithmetic
* `a + b` : a plus b
* `a + b + c + d + e` : sum of all five timeseries
* `a - b` : a minus b, e.g. the difference between inflow and outflow
* `a * b` : a times b
* `a / b` : a divided by b
* `a * 2.5` : a times 2.5
* `-a` : a with the opposite sign (+/- key)
* `(a + b) / 2` : mean (average) of a and b
* `(a + b + c) / 3` : mean of a, b and c
* `1 / a` : reciprocal of a (1/x key)
* `a % 60` : remainder when dividing a by 60, e.g. the minutes after the full hours of a duration
  in minutes

### Percent
* `a * 19 / 100` : 19 percent of a
* `a * 1.19` : a plus 19 percent
* `a * (1 - 0.25)` : a minus 25 percent
* `a / b * 100` : a as percentage of b
* `(b - a) / a * 100` : change from a to b in percent

### Powers and roots
* `a**2` : a squared (x² key)
* `a**3` : a cubed
* `a**b` : a to the power of b (xʸ key)
* `10**a` : 10 to the power of a (10ˣ key)
* `sqrt(a)` : square root of a (√ key, Excel: SQRT)
* `a**(1/3)` : cube root of a
* `a**(1/b)` : b-th root of a
* `sqrt(a**2 + b**2)` : hypotenuse of a right triangle with the sides a and b (Pythagoras)

### Logarithms and exponential function
* `log(a)` : natural logarithm of a (ln key, Excel: LN)
* `log10(a)` : logarithm of a to base 10 (log key, Excel: LOG)
* `log(a) / log(2)` : logarithm of a to base 2
* `log(a) / log(b)` : logarithm of a to base b
* `exp(a)` : e to the power of a (eˣ key, Excel: EXP)
* `exp(1) * a` : a times Euler's number e = 2.71828...

### Absolute value and rounding
* `abs(a)` : absolute value of a, i.e. a without its sign (Excel: ABS)
* `abs(a - b)` : distance between a and b, always positive
* `a.round(2)` : a rounded to 2 decimal places
* `a.round()` : a rounded to a whole number. Values exactly in the middle are rounded to the even
  number, e.g. 2.5 becomes 2 and 3.5 becomes 4.
* `floor(a + 0.5)` : a rounded to a whole number like with Excel's ROUND(a, 0) for positive
  numbers, e.g. 2.5 becomes 3
* `floor(a * 100 + 0.5) / 100` : a rounded to 2 decimal places like with Excel's ROUND(a, 2) for
  positive numbers
* `floor(a)` : a rounded down to a whole number, e.g. 2.7 becomes 2 and -2.3 becomes -3 (Excel:
  INT)
* `ceil(a)` : a rounded up to a whole number, e.g. 2.3 becomes 3 and -2.7 becomes -2
* `floor(a / 15) * 15` : a rounded down to a multiple of 15

### Angles (trigonometry)
Like in Excel, angles are in radians. A full circle has 2 times π radians, which is 360 degrees.
* `sin(a)` : sine of the angle a in radians (also `cos(a)` and `tan(a)`)
* `sin(a * pi / 180)` : sine of the angle a in degrees (also with cos and tan)
* `arcsin(a)` : angle in radians whose sine is a (sin⁻¹ key, also `arccos(a)` and `arctan(a)`)
* `arcsin(a) * 180 / pi` : angle in degrees whose sine is a
* `arctan2(b, a)` : angle in radians of the point with x-coordinate a and y-coordinate b (Excel:
  ATAN2(a, b))
* `a * 180 / pi` : angle a converted from radians to degrees
* `a * pi / 180` : angle a converted from degrees to radians
* `sinh(a)` : hyperbolic sine of a (also `cosh`, `tanh`, `arcsinh`, `arccosh` and `arctanh`)

### Comparisons
A comparison results in True or False for each point in time.
* `a > 100` : True where a is greater than 100 (also `>=`, `<` and `<=`)
* `a == b` : True where a equals b
* `a != 0` : True where a is not 0
* `10 < a < 20` : True where a is between 10 and 20
* `a.between(10, 20)` : True where a is between 10 and 20, including 10 and 20
* `a > 10 and b > 10` : True where both are greater than 10 (Excel: AND)
* `a > 10 or b > 10` : True where at least one of them is greater than 10 (Excel: OR)
* `not a > 10` : True where a is not greater than 10 (Excel: NOT)

### Conditions, limits, larger and smaller value
* `a.where(c > 0, b)` : a where c is greater than 0, otherwise b (Excel: IF(c > 0, a, b))
* `a.where(a > 0, 0)` : a where a is greater than 0, otherwise 0 (Excel: IF(a > 0, a, 0))
* `a.where(a > 0)` : a where a is greater than 0, otherwise no value, e.g. to leave out invalid
  values
* `a.clip(0, 100)` : a limited to the range from 0 to 100, i.e. values below 0 become 0 and
  values above 100 become 100
* `a.clip(lower=b)` : the larger value of a and b (Excel: MAX(a, b))
* `a.clip(upper=b)` : the smaller value of a and b (Excel: MIN(a, b))
* `(a > 0) * a` : also a where a is greater than 0, otherwise 0, since True counts as 1 and False
  as 0 in calculations

### Statistics of a timeseries
Methods like `a.mean()` calculate a single value from all values of the timeseries a. Use them in
a formula, so that the result is a timeseries again. Such methods are `mean` (mean), `median`,
`std` (standard deviation), `var` (variance), `min`, `max`, `sum`, `count` (number of values) and
`quantile`.
* `a - a.mean()` : deviation of a from its mean
* `(a - a.mean()) / a.std()` : standardized values (z-score), i.e. the deviation from the mean in
  multiples of the standard deviation
* `abs(a - a.mean()) > 3 * a.std()` : True where a deviates from its mean by more than 3 standard
  deviations, e.g. to find outliers
* `a / a.max() * 100` : a in percent of its largest value
* `(a - a.min()) / (a.max() - a.min())` : a scaled to the range from 0 to 1
* `a / a.sum() * 100` : share of each value in the sum of all values in percent
* `a > a.quantile(0.9)` : True for the highest 10 percent of the values
* `a * 0 + a.mean()` : the mean of a at each point in time, e.g. to show it as a line in a plot

### Values over time
These methods calculate a value at each point in time from the values before:
* `a.diff()` : change from the previous value
* `a.shift(1)` : the previous value of a
* `a.pct_change() * 100` : change from the previous value in percent
* `a.cumsum()` : running total of a
* `a.cummax()` : the largest value so far (also `a.cummin()`)
* `a.rolling(5).mean()` : moving average of the last 5 values (the first 4 points in time have no
  value)
* `a.rolling("1h").mean()` : moving average of the values of the last hour (durations like
  `"15min"`, `"1h"` or `"1D"` are written in quotes)
* `a.rolling(5).std()` : moving standard deviation of the last 5 values (also `max`, `min`, `sum`
  and `median` instead of `std`)
* `a.ewm(span=10).mean()` : exponentially weighted moving average, in which recent values count
  more
* `a.resample("1h").mean()` : hourly means with one value per hour (also `"15min"` or `"1D"` and
  `sum`, `max` or `min` instead of `mean`)
* `a.resample("1D").sum()` : daily totals (days from midnight to midnight in the time zone of a,
  see the examples for time zones)

### Time zones
Days start at midnight in the time zone in which the timeseries should be evaluated according to
their metadata (`default_timezone`), e.g. in German time for timeseries from a plant in Germany,
also on the days with 23 or 25 hours on which daylight saving time starts or ends. The same
applies to hours of the day, weekdays, weeks and months. For this, the timeseries used in the
formula are converted to this time zone before the calculation. If their metadata specify
different time zones, the formula is calculated in UTC. Timeseries without metadata, e.g. manual
inputs, are calculated in UTC as well, or in the time zone of the other timeseries. With the input
time_zone_from_metadata switched off (False), the timeseries are not converted, so that the
formula is calculated in the time zones they have, usually UTC. The result has its points in time
in UTC again, like the timeseries of data sources, e.g. the daily total of 28
March in German time at 23:00 UTC on 27 March.

`modify_timezone(a, "Europe/Berlin")` converts the points in time of a to German time, e.g. for
timeseries without metadata. Points in time without a time zone are taken as German time then.
Other time zones are written like `"Europe/London"` or `"UTC"`.
* `a.groupby(pd.Grouper(freq="D")).cumsum()` : running total of a, which starts again at midnight
  every day
* `a.where(a.index.hour < 6)` : a only from midnight to 6:00
* `a.where(a.index.day_of_week < 5)` : a only from Monday to Friday
* `modify_timezone(a, "Europe/Berlin").resample("1D").sum()` : daily totals for the days in German
  time, also if the metadata of a specify no or another time zone
* `modify_timezone(a, "UTC").resample("1D").sum()` : daily totals for the days in UTC

### Missing values
* `a.fillna(0)` : a with 0 instead of missing values
* `a.fillna(b)` : a with the values of b instead of missing values
* `a.ffill()` : a with the previous value instead of missing values
* `a.interpolate(method="time")` : a with missing values filled in on a straight line between the
  values before and after
* `a.dropna()` : a without the points in time with missing values
* `a.isna()` : True where a value of a is missing

`a + b` has no value where a value of a or b is missing, and no value at all if b has no values.
With the following formulas, missing values count as 0 instead, like empty cells in Excel:
* `a.add(b, fill_value=0)` : a plus b, in which a missing value of a or b counts as 0. Only
  where both values are missing, the result is missing, too.
* `a.sub(b, fill_value=0)` : a minus b, in which a missing value of a or b counts as 0
* `abcde.sum(axis=1, min_count=1)` : sum of all connected timeseries at each point in time, in
  which missing values count as 0. Only where all values are missing, the result is missing, too
  (with `abcde.sum(axis=1)` it is 0 there).
* `a.resample("1h").mean().add(b.resample("1h").mean(), fill_value=0)` : sum of the hourly means
  of a and b, e.g. for timeseries with different points in time. If a or b has no values in an
  hour, its hourly mean counts as 0.
* `abcde.resample("1h").mean().sum(axis=1, min_count=1)` : sum of the hourly means of all
  connected timeseries, in which missing hourly means count as 0

### Several timeseries at each point in time
`abcde` is a table with all connected timeseries as columns a, b, c, d and e. With `axis=1`, its
methods calculate one value from the values of all connected timeseries at each point in time.
Missing values are left out.
* `abcde.mean(axis=1)` : mean of the timeseries at each point in time (Excel: AVERAGE)
* `abcde.std(axis=1)` : standard deviation of the timeseries at each point in time (Excel:
  STDEV.S)
* `abcde.max(axis=1)` : largest value at each point in time (Excel: MAX)
* `abcde.min(axis=1)` : smallest value at each point in time (Excel: MIN)
* `abcde.max(axis=1) - abcde.min(axis=1)` : difference between the largest and the smallest value
* `abcde.sum(axis=1)` : sum of the timeseries at each point in time, in which missing values count
  as 0 (Excel: SUM)
* `abcde.median(axis=1)` : median of the timeseries at each point in time (Excel: MEDIAN)
* `abcde.count(axis=1)` : number of timeseries with a value at each point in time

### Metadata
Timeseries from data sources like the hetida platform come with metadata, e.g. their unit, the
number of decimal places to show them with and the properties of their signals. `meta.a.max` is
the field max of the metadata of a, e.g. the property max of the signal connected to a. Write
fields whose names contain spaces or other special characters in square brackets and quotes, e.g.
`meta.a["upper limit"]`. Uppercase and lowercase letters matter here, too. If the metadata do not
contain a field, the error message lists the fields they contain.
* `a > meta.a.max` : True where a is larger than its property max
* `a.where(a <= meta.a.max)` : a without the values larger than its property max, e.g. to leave
  out implausible values
* `a.clip(lower=meta.a.min, upper=meta.a.max)` : a limited to the range from its property min to
  its property max
* `a / meta.a.max * 100` : a in percent of its property max
* `(a - meta.a.min) / (meta.a.max - meta.a.min) * 100` : position of a in the range from its
  property min to its property max in percent
* `a.round(meta.a.decimals)` : a rounded to the number of decimal places of its metadata
* `a.resample("1D").agg(meta.a.default_aggregation_method.lower())` : daily values of a,
  aggregated with the aggregation method of its metadata, e.g. the mean or the sum

The functions of hdhelpers for metadata can be used as well, e.g. for the period for which the
timeseries were queried, see the
[hdhelpers documentation](https://hetida.github.io/hdhelpers/index.html#module-hdhelpers.metadata):
* `a > hdhelpers.metadata.get_series_info(a, "max")` : the same as `a > meta.a.max`
* `a.reindex(pd.date_range(hdhelpers.metadata.get_queried_interval(a)[0], hdhelpers.metadata.get_queried_interval(a)[1], freq=meta.a.data_frequency, inclusive="left"))` :
  a at all points in time of the queried period according to its data frequency, with missing
  values where a has no value, e.g. to find gaps

### Everyday examples
* `a * 1000` : cubic meters to liters
* `a / 3.6` : km/h to m/s
* `a * 9 / 5 + 32` : degrees Celsius to degrees Fahrenheit
* `a + 273.15` : degrees Celsius to Kelvin
* `a * b / 1000` : electric power in kW from the voltage a in V and the current b in A
* `b / a * 100` : efficiency in percent from the power input a and the power output b
* `pi * a**2 / 4` : area of a circle with the diameter a
* `a * b * c` : volume of a box with the length a, the width b and the height c

## Good to know
* **Points in time**: Values of different timeseries are only combined at exactly the same
  points in time. If a point in time exists in a, but not in b, the result of `a + b` has no
  value there. If your timeseries have different points in time, first bring them to common
  points in time, e.g. with `a.resample("15min").mean() + b.resample("15min").mean()` or with the
  component "Resample Datetime Index using Mean".
* **Days** start at midnight in the time zone of the metadata of the timeseries, otherwise in UTC,
  see the examples for time zones. The input time_zone_from_metadata switches this off. The
  result is in UTC.
* **Missing values**: Where a value is missing, the result is missing, too, except for methods
  which leave out missing values like `a.mean()` or `abcde.mean(axis=1)`. To count missing values
  as 0, use e.g. `a.add(b, fill_value=0)` instead of `a + b`, see the examples for missing values.
* **Impossible calculations** like a division by 0, the square root of a negative number or the
  logarithm of 0 do not stop the calculation. The result is then missing or infinite at this
  point in time (NaN or inf, both are shown as null in the result view).
* **e** is the fifth input, not Euler's number 2.71828... Use `exp(1)` for Euler's number and
  `exp(a)` for e to the power of a.
* **True and False** values of an input count as 1 and 0.
* **Error messages** tell you what to change, e.g. if the formula uses b but nothing is connected
  to the input b.

## Details
The formula is calculated with the pandas function eval, see the
[pandas documentation of eval](https://pandas.pydata.org/docs/reference/api/pandas.eval.html)
and its [supported syntax](https://pandas.pydata.org/docs/user_guide/enhancingperf.html#supported-syntax).
Everything it supports can be used, in particular the methods of the timeseries, which are
pandas Series, and of `abcde`, which is a pandas DataFrame, see the
[pandas documentation of Series](https://pandas.pydata.org/docs/reference/series.html) and
[of DataFrame](https://pandas.pydata.org/docs/reference/frame.html). The functions are `sqrt`,
`exp`, `expm1`, `log`, `log1p`, `log10`, `abs`, `floor`, `ceil`, `sin`, `cos`, `tan`, `arcsin`,
`arccos`, `arctan`, `arctan2`, `sinh`, `cosh`, `tanh`, `arcsinh`, `arccosh` and `arctanh`. In
addition to pandas eval, `pi`, `abcde`, `meta`, the Python libraries pandas as `pd`, numpy as `np`
and hdhelpers as `hdhelpers` and the function `modify_timezone` of hdhelpers can be used, see the
[hdhelpers documentation](https://hetida.github.io/hdhelpers/), and the formula may start with
`=`.

`meta.a.max` reads the field max of the metadata of a as specified by the
[metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/):
A field is looked up in the value dimension "value", in the metric, in `value_dimensions_shared`
and finally in the properties the metric inherits (`inherited`), in which the hetida platform
provides the properties of signals. Fields the conventions define for the timeseries itself, like
`unit`, are not taken from the inherited properties. The fields on how the values are recorded,
like `data_frequency`, and `default_timezone` fall back to the dataset metadata.

The values of the inputs are converted to floating point numbers before the calculation. They keep
their names and metadata, so that e.g. the functions of hdhelpers can read their metadata. The
result has neither a name nor metadata, since the formula calculates a new quantity.

The formula is calculated in the `default_timezone` of the timeseries used in it (with the
fallback to the dataset metadata) if all of them which have one specify the same, otherwise in
UTC. For this, the points in time of these timeseries are converted to this time zone, unless they
have no time zone or time_zone_from_metadata is False. The points in time of the result are converted to UTC if they have a time zone, since e.g. generic
REST adapters only accept timeseries in UTC.
"""

import ast
import dataclasses
import types
import warnings
from typing import Any

import hdhelpers
import numpy as np
import pandas as pd
import pytest
from hdhelpers.metadata import (
    Recording,
    attach_metadata,
    attrs_to_json,
    get_series_default_aggregation_method,
    get_series_default_timezone,
    get_series_info,
    get_series_recording,
    read_metadata,
)
from hdhelpers.metadata.conventions import MetricMetadata, ValueDimensionMetadata

from hdutils import ComponentInputValidationException, parse_value

SERIES_INPUT_NAMES = ("a", "b", "c", "d", "e")

# The functions of pandas eval with their number of arguments
FUNCTIONS = dict.fromkeys(
    (
        "sqrt",
        "exp",
        "expm1",
        "log",
        "log1p",
        "log10",
        "abs",
        "floor",
        "ceil",
        "sin",
        "cos",
        "tan",
        "arcsin",
        "arccos",
        "arctan",
        "sinh",
        "cosh",
        "tanh",
        "arcsinh",
        "arccosh",
        "arctanh",
    ),
    1,
) | {"arctan2": 2}

CONSTANTS = {"pi": np.pi}

# The Python libraries pandas, numpy and hdhelpers, e.g. for pd.Grouper(freq="D"), np.sign(a) or
# the metadata functions of hdhelpers in a formula
MODULES = {"pd": pd, "np": np, "hdhelpers": hdhelpers}

# Functions of hdhelpers, which are called in Python, unlike the FUNCTIONS of pandas eval, e.g.
# for modify_timezone(a, "Europe/Berlin") in a formula
HELPER_FUNCTIONS = {"modify_timezone": hdhelpers.modify_timezone}

# The names formulas can use in addition to the inputs, abcde and meta
PREDEFINED_NAMES = CONSTANTS | MODULES | HELPER_FUNCTIONS

# The name of the table (DataFrame) of all connected timeseries, e.g. for abcde.mean(axis=1)
DATAFRAME_NAME = "abcde"

# The name of the metadata of the connected timeseries, e.g. for meta.a.max
METADATA_NAME = "meta"

# Fields of the metadata conventions which describe a timeseries itself, like its unit, and are
# therefore not taken from the properties it inherits, e.g. from the plant a sensor belongs to
OWN_METADATA_FIELDS = (
    set(MetricMetadata.model_fields) | set(ValueDimensionMetadata.model_fields)
) - {"inherited"}

# Fields of the metadata conventions on how the values are recorded, which fall back to the
# dataset metadata
RECORDING_FIELDS = tuple(field.name for field in dataclasses.fields(Recording))

# Formulas replacing functions known from Excel (English and German names) and calculators, by
# lowercase name
REPLACEMENTS = {
    "wurzel": "sqrt(a)",
    "ln": "log(a)",
    "log": "log10(a)",  # Excel's LOG is the logarithm to base 10
    "power": "a**b",
    "potenz": "a**b",
    "round": "a.round(2)",
    "runden": "a.round(2)",
    "int": "floor(a)",
    "ganzzahl": "floor(a)",
    "mod": "a % b",
    "rest": "a % b",
    "sum": "abcde.sum(axis=1)",
    "summe": "abcde.sum(axis=1)",
    "average": "abcde.mean(axis=1)",
    "mittelwert": "abcde.mean(axis=1)",
    "median": "abcde.median(axis=1)",
    "max": "abcde.max(axis=1)",
    "min": "abcde.min(axis=1)",
    "stdev": "abcde.std(axis=1)",
    "stabw": "abcde.std(axis=1)",
    "count": "abcde.count(axis=1)",
    "anzahl": "abcde.count(axis=1)",
    "if": "a.where(c > 0, b)",
    "wenn": "a.where(c > 0, b)",
    "and": "a > 0 and b > 0",
    "und": "a > 0 and b > 0",
    "or": "a > 0 or b > 0",
    "oder": "a > 0 or b > 0",
    "not": "not a > 0",
    "nicht": "not a > 0",
    "pi": "pi",
    "asin": "arcsin(a)",
    "acos": "arccos(a)",
    "atan": "arctan(a)",
    "asinh": "arcsinh(a)",
    "acosh": "arccosh(a)",
    "atanh": "arctanh(a)",
    "atan2": "arctan2(b, a)",  # Excel's ATAN2(a, b)
    "arctan2": "arctan2(b, a)",
}

MESSAGES = {
    "empty": "Please enter a formula, e.g. (a + b) / 2.",
    "syntax": (
        "The formula cannot be read. Please check: Are all brackets closed? Is there a * between"
        " numbers and letters, e.g. 2 * a instead of 2a? Decimal numbers are written with a"
        " point, e.g. 1.5, comparisons with == and != instead of = and <>, and percent as / 100,"
        " e.g. a * 19 / 100."
    ),
    "power": "Powers are written with ** instead of ^, e.g. a**2 for a squared.",
    "decimal_comma": (
        "Decimal numbers are written with a point instead of a comma: 1.5 instead of 1,5."
    ),
    "not_connected": (
        "The formula uses {name}, but there is no timeseries connected to the input {name}."
    ),
    "not_connected_e": " For Euler's number 2.71828... write exp(1).",
    "uppercase_input": "The inputs are written in lowercase letters: {lower} instead of {name}.",
    "unknown_name": (
        "{name} is unknown. The formula can use the inputs a, b, c, d, e (in lowercase letters),"
        " the table abcde of all of them, their metadata like meta.a.max, numbers, the number pi,"
        " the function modify_timezone and the Python libraries pandas as pd, numpy as np and"
        " hdhelpers."
    ),
    "metadata_input": (
        "meta is followed by the input whose metadata the formula uses, e.g. meta.a.max for the"
        " field max of the metadata of a."
    ),
    "metadata_field": (
        "meta.{name} is followed by the field of the metadata the formula uses, e.g."
        " meta.{name}.max."
    ),
    "no_metadata": (
        "The timeseries connected to the input {name} has no metadata, or its metadata do not"
        " follow the metadata conventions of hetida designer."
    ),
    "unknown_metadata": (
        "The metadata of {name} contain no field {field}. Available fields: {fields}. Write"
        ' fields with spaces or other special characters like meta.{name}["upper limit"].'
    ),
    "nothing_connected": (
        "The formula uses abcde, but there is no timeseries connected to any of the inputs a, b,"
        " c, d, e."
    ),
    "function_without_brackets": "{name} is a function and needs brackets, e.g. {example}.",
    "unknown_function": "The function {name} does not exist here.",
    "replacement": " Write for example {replacement} instead.",
    "functions": " Available functions: {functions}.",
    "multiplication": "Multiplying needs a *, e.g. a * (b + c) instead of a(b + c).",
    "one_value": "{name} needs exactly one value in its brackets, e.g. {example}.",
    "two_values": (
        "{name} needs exactly two values in its brackets, separated by a comma, e.g. {example}."
    ),
    "log_base": " The logarithm to another base is calculated like log(a) / log(2) for base 2.",
    "not_numbers": (
        "The timeseries connected to the input {name} has values which are not numbers."
    ),
    "no_timeseries": (
        "The formula does not calculate a timeseries. Use at least one of the inputs a, b, c, d,"
        " e, e.g. a * 2. Single values like a.mean() can be used in a formula, e.g. a - a.mean()."
    ),
    "failed": "The formula could not be calculated: {error}",
}


@dataclasses.dataclass(frozen=True)
class Language:
    """The texts of the formula calculator in a language

    "Formelrechner", the German version of this component, imports this component and calculates
    formulas with German texts.
    """

    # the name of the formula input, which errors report as invalid for mistakes in the formula
    formula_input_name: str
    # the messages explaining mistakes, by the keys of MESSAGES
    messages: dict[str, str]


ENGLISH = Language(formula_input_name="formula", messages=MESSAGES)


def invalid_input_error(message: str, input_name: str) -> ComponentInputValidationException:
    return ComponentInputValidationException(
        message, error_code=422, invalid_component_inputs=[input_name]
    )


def formula_error(message: str, language: Language) -> ComponentInputValidationException:
    return invalid_input_error(message, language.formula_input_name)


def function_example(name: str) -> str:
    """
    >>> function_example("sqrt")
    'sqrt(a)'
    >>> function_example("arctan2")
    'arctan2(b, a)'
    """
    return "arctan2(b, a)" if FUNCTIONS[name] == 2 else f"{name}(a)"


def check_function_call(call: ast.Call, language: Language) -> None:
    """Explain mistakes in calls of functions like sqrt(a)

    pandas eval only knows the functions in FUNCTIONS, in addition to methods like a.mean().
    The HELPER_FUNCTIONS are called in Python like methods.
    """
    if not isinstance(call.func, ast.Name) or call.func.id in SERIES_INPUT_NAMES:
        # a missing * between a number or input and a bracket, like in 2(a + b) or a(b + c)
        raise formula_error(language.messages["multiplication"], language)
    name = call.func.id
    if name in HELPER_FUNCTIONS:
        # Python checks the values in the brackets
        return
    if name not in FUNCTIONS:
        replacement = REPLACEMENTS.get(name.lower())
        if replacement is None and name.lower() in FUNCTIONS:
            replacement = function_example(name.lower())
        raise formula_error(
            language.messages["unknown_function"].format(name=name)
            + (
                language.messages["replacement"].format(replacement=replacement)
                if replacement is not None
                else language.messages["functions"].format(
                    functions=", ".join([*FUNCTIONS, *HELPER_FUNCTIONS])
                )
            ),
            language,
        )
    if len(call.args) != FUNCTIONS[name]:
        message = language.messages["one_value" if FUNCTIONS[name] == 1 else "two_values"].format(
            name=name, example=function_example(name)
        )
        if name in ("log", "log10") and len(call.args) == 2:
            message += language.messages["log_base"]
        if len(call.args) > FUNCTIONS[name]:
            message += " " + language.messages["decimal_comma"]
        raise formula_error(message, language)


def check_name(name: str, series_inputs: dict[str, pd.Series | None], language: Language) -> None:
    if name in SERIES_INPUT_NAMES:
        if series_inputs[name] is None:
            raise invalid_input_error(
                language.messages["not_connected"].format(name=name)
                + (language.messages["not_connected_e"] if name == "e" else ""),
                name,
            )
    elif name == DATAFRAME_NAME:
        if all(series is None for series in series_inputs.values()):
            raise formula_error(language.messages["nothing_connected"], language)
    elif name == METADATA_NAME:
        # without an input, which check_node checks for meta.a
        raise formula_error(language.messages["metadata_input"], language)
    elif name in PREDEFINED_NAMES:
        return
    elif name.lower() in SERIES_INPUT_NAMES:
        raise formula_error(
            language.messages["uppercase_input"].format(name=name, lower=name.lower()), language
        )
    elif name.lower() in FUNCTIONS:
        raise formula_error(
            language.messages["function_without_brackets"].format(
                name=name, example=function_example(name.lower())
            ),
            language,
        )
    else:
        raise formula_error(language.messages["unknown_name"].format(name=name), language)


def metadata_input(node: ast.AST) -> str | None:
    """The input whose metadata the node is, e.g. a for meta.a, None for other nodes"""
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == METADATA_NAME
    ):
        return node.attr
    return None


def check_metadata_input(
    input_name: str, series_inputs: dict[str, pd.Series | None], language: Language
) -> None:
    if input_name not in SERIES_INPUT_NAMES:
        raise formula_error(language.messages["metadata_input"], language)
    check_name(input_name, series_inputs, language)


def check_node(
    node: ast.AST, series_inputs: dict[str, pd.Series | None], language: Language
) -> None:
    """Explain typical mistakes in the formula, which pandas eval reports less helpfully

    Everything else, e.g. methods like a.mean(), is left to pandas eval.
    """
    if (
        isinstance(node, ast.Attribute | ast.Subscript)
        and (input_name := metadata_input(node.value)) is not None
    ):
        # a field of the metadata, e.g. meta.a.max or meta.a["upper limit"]
        check_metadata_input(input_name, series_inputs, language)
        children = [node.slice] if isinstance(node, ast.Subscript) else []
    elif (input_name := metadata_input(node)) is not None:
        # meta.a without a field
        check_metadata_input(input_name, series_inputs, language)
        raise formula_error(language.messages["metadata_field"].format(name=input_name), language)
    elif isinstance(node, ast.Call) and not isinstance(node.func, ast.Attribute):
        check_function_call(node, language)
        children = [*node.args, *node.keywords]
    elif isinstance(node, ast.Name):
        check_name(node.id, series_inputs, language)
        children = []
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitXor):
        raise formula_error(language.messages["power"], language)
    else:
        children = list(ast.iter_child_nodes(node))
    for child in children:
        check_node(child, series_inputs, language)


def as_numbers(series: pd.Series, input_name: str, language: Language) -> pd.Series:
    """The values of the series as floating point numbers, with its name and metadata"""
    try:
        numbers = pd.to_numeric(series).astype("float64")
    except (ValueError, TypeError) as error:
        raise invalid_input_error(
            language.messages["not_numbers"].format(name=input_name), input_name
        ) from error
    # which pd.to_numeric drops, e.g. for hdhelpers.metadata.get_series_info(a, "max")
    numbers.attrs = series.attrs
    return numbers


def calculation_time_zone(inputs: list[pd.Series]) -> str:
    """The time zone in which the formula is calculated, e.g. for days from midnight to midnight

    The default_timezone of the metadata of the inputs if those which have one agree on it,
    otherwise UTC. Inputs without, e.g. manual inputs, do not count.
    """
    time_zones = {
        time_zone
        for series in inputs
        if (time_zone := get_series_default_timezone(series)) is not None
    }
    return time_zones.pop() if len(time_zones) == 1 else "UTC"


def in_time_zone(series: pd.Series, time_zone: str) -> pd.Series:
    """The series with its points in time converted to the time zone, if they have a time zone"""
    if isinstance(series.index, pd.DatetimeIndex) and series.index.tz is not None:
        return series.tz_convert(time_zone)
    return series


def metadata_value(series: pd.Series, field: str) -> Any:
    """A field of the metadata of the series, None if it is missing

    The field is looked up as specified in "Fallbacks and inherited properties" of
    https://hetida.github.io/hetida-designer/user_guide/attached_metadata/
    """
    if field in RECORDING_FIELDS:
        return getattr(get_series_recording(series), field)
    if field == "default_timezone":
        return get_series_default_timezone(series)
    if field == "default_aggregation_method":
        return get_series_default_aggregation_method(series)
    return get_series_info(series, field, include_inherited=field not in OWN_METADATA_FIELDS)


def metadata_fields(series: pd.Series) -> list[str]:
    """The fields of the metadata of the series which have a single value, like a number"""
    attrs = attrs_to_json(series.attrs)
    fields = [*RECORDING_FIELDS, "default_timezone", "default_aggregation_method"]
    for metric in attrs.get("metrics") or []:
        fields += metric
        fields += metric.get("inherited") or {}
        for value_dimension in [
            *(metric.get("value_dimensions") or []),
            *(attrs.get("value_dimensions_shared") or []),
        ]:
            if value_dimension.get("column") == "value":
                fields += value_dimension
    return sorted(
        (
            field
            for field in set(fields)
            if isinstance(metadata_value(series, field), bool | int | float | str)
        ),
        key=str.lower,
    )


class MissingMetadataError(Exception):
    def __init__(self, input_name: str, field: str):
        super().__init__(f"The metadata of {input_name} contain no field {field}")
        self.input_name = input_name
        self.field = field


class MissingMetadataAttributeError(MissingMetadataError, AttributeError):
    """An AttributeError, as which pandas eval expects missing attributes

    pandas eval checks e.g. whether values have a dtype.
    """


class Metadata:
    """The metadata of the timeseries connected to an input, e.g. meta.a

    Its fields are its attributes, e.g. meta.a.max, and items, e.g. meta.a["upper limit"].
    """

    def __init__(self, input_name: str, series: pd.Series):
        self._input_name = input_name
        self._series = series

    def __getattr__(self, field: str) -> Any:
        if field.startswith("_"):
            # e.g. pandas checking for its internal attributes, or copy and pickle before
            # _series is set. Such fields are written like meta.a["_field"].
            raise AttributeError(field)
        if (value := metadata_value(self._series, field)) is None:
            raise MissingMetadataAttributeError(self._input_name, field)
        return value

    def __getitem__(self, field: str) -> Any:
        if (value := metadata_value(self._series, field)) is None:
            raise MissingMetadataError(self._input_name, field)
        return value


def missing_metadata_error(
    input_name: str, field: str, series: pd.Series, language: Language
) -> ComponentInputValidationException:
    if read_metadata(series, "SERIES") is None:
        return invalid_input_error(
            language.messages["no_metadata"].format(name=input_name), input_name
        )
    return formula_error(
        language.messages["unknown_metadata"].format(
            name=input_name, field=field, fields=", ".join(metadata_fields(series))
        ),
        language,
    )


def calculate(
    formula: str | None,
    series_inputs: dict[str, pd.Series | None],
    language: Language,
    *,
    time_zone_from_metadata: bool,
) -> pd.Series:
    """The result of the formula, calculated from the series inputs a, b, c, d and e

    Calculates the formula in the time zone of the metadata of the inputs if
    time_zone_from_metadata is True. Explains mistakes in the formula in the given language.
    """
    # in one line, since pandas eval does not calculate formulas spanning several lines
    expression = " ".join((formula or "").split()).removeprefix("=").strip()
    if expression == "":
        raise formula_error(language.messages["empty"], language)
    try:
        with warnings.catch_warnings():
            # e.g. "'int' object is not callable" for 2(a + b), which is explained below
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise formula_error(language.messages["syntax"], language) from error
    if isinstance(tree.body, ast.Tuple):
        # e.g. a * 1,5
        raise formula_error(language.messages["decimal_comma"], language)
    check_node(tree, series_inputs, language)

    used_names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    numbers = {
        name: as_numbers(series, name, language)
        for name, series in series_inputs.items()
        if series is not None and (name in used_names or DATAFRAME_NAME in used_names)
    }
    if time_zone_from_metadata:
        time_zone = calculation_time_zone([series_inputs[name] for name in numbers])
        numbers = {name: in_time_zone(series, time_zone) for name, series in numbers.items()}
    variables = {name: numbers[name] for name in SERIES_INPUT_NAMES if name in used_names}
    if DATAFRAME_NAME in used_names:
        variables[DATAFRAME_NAME] = pd.concat(numbers, axis=1, sort=True)
    if METADATA_NAME in used_names:
        variables[METADATA_NAME] = types.SimpleNamespace(
            **{
                name: Metadata(name, series)
                for name, series in series_inputs.items()
                if series is not None
            }
        )
    try:
        # numpy warns about impossible calculations if pandas eval does not use numexpr
        with np.errstate(all="ignore"):
            # the expression, not ast.unparse(tree), since pandas eval gives & and | a lower
            # precedence than Python, so that dropping brackets could change the result
            result = pd.eval(expression, local_dict=variables | PREDEFINED_NAMES, global_dict={})
    except MissingMetadataError as error:
        raise missing_metadata_error(
            error.input_name, error.field, series_inputs[error.input_name], language
        ) from error
    except Exception as error:  # noqa: BLE001 # pandas eval raises various exceptions
        raise formula_error(language.messages["failed"].format(error=error), language) from error
    if not isinstance(result, pd.Series):
        raise formula_error(language.messages["no_timeseries"], language)
    if isinstance(result.index, pd.DatetimeIndex) and result.index.tz is not None:
        # e.g. after modify_timezone(a, "Europe/Berlin"), since e.g. generic REST adapters only
        # accept timeseries in UTC
        result = result.tz_convert("UTC")
    result = result.rename(None)
    result.attrs = {}
    return result


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "a": {"data_type": "SERIES", "default_value": None},
        "b": {"data_type": "SERIES", "default_value": None},
        "c": {"data_type": "SERIES", "default_value": None},
        "d": {"data_type": "SERIES", "default_value": None},
        "e": {"data_type": "SERIES", "default_value": None},
        "formula": {"data_type": "STRING"},
        "time_zone_from_metadata": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "result": {"data_type": "SERIES"},
    },
    "name": "Formula Calculator",
    "category": "Basic Arithmetic",
    "description": "Calculates a formula like in Excel with up to five timeseries a, b, c, d, e",
    "version_tag": "0.1.0",
    "id": "1e0e71d0-cd86-4068-bf11-19df7d002737",
    "revision_group_id": "c5f1b53a-b2ce-4833-a108-4c38d4a53b9d",
    "state": "RELEASED",
    "released_timestamp": "2026-11-12T12:10:05+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    formula,
    a=parse_default_value(COMPONENT_INFO, "a"),
    b=parse_default_value(COMPONENT_INFO, "b"),
    c=parse_default_value(COMPONENT_INFO, "c"),
    d=parse_default_value(COMPONENT_INFO, "d"),
    e=parse_default_value(COMPONENT_INFO, "e"),
    time_zone_from_metadata=True,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "result": calculate(
            formula,
            {"a": a, "b": b, "c": c, "d": d, "e": e},
            ENGLISH,
            time_zone_from_metadata=time_zone_from_metadata,
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "a",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 10.0, "2026-01-01T01:00:00Z": 20.0, "2026-01-01T02:00:00Z": 30.0}'
            },
        },
        {
            "workflow_input_name": "b",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 30.0, "2026-01-01T01:00:00Z": 50.0, "2026-01-01T02:00:00Z": 40.0}'
            },
        },
        {
            "workflow_input_name": "c",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "d",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "e",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {"workflow_input_name": "formula", "filters": {"value": "(a + b) / 2"}},
        {
            "workflow_input_name": "time_zone_from_metadata",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "a",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 10.0, "2026-01-01T01:00:00Z": 20.0, "2026-01-01T02:00:00Z": 30.0}'
            },
        },
        {
            "workflow_input_name": "b",
            "filters": {
                "value": '{"2026-01-01T00:00:00Z": 30.0, "2026-01-01T01:00:00Z": 50.0, "2026-01-01T02:00:00Z": 40.0}'
            },
        },
        {
            "workflow_input_name": "c",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "d",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "e",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {"workflow_input_name": "formula", "filters": {"value": "(a + b) / 2"}},
        {
            "workflow_input_name": "time_zone_from_metadata",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
    ]
}


# Unit tests, see https://hetida.github.io/hetida-designer/user_guide/component_writing/unit_testing/
# ruff: noqa: S101


def timeseries(*values):
    return pd.Series(
        values,
        index=pd.date_range("2026-01-01T00:00:00Z", periods=len(values), freq="h"),
        dtype="float64",
    )


def test_run_with_test_wiring():
    result = main(
        **{
            inp_wiring["workflow_input_name"]: parse_value(
                inp_wiring["filters"]["value"],
                COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]]["data_type"],
                nullable=True,
            )
            for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
        }
    )["result"]

    pd.testing.assert_series_equal(result, timeseries(20.0, 35.0, 35.0), check_freq=False)


def documented_example_formulas():
    examples = __doc__.split("\n## Examples\n")[1].split("\n## Good to know\n")[0]
    return [line.split("`")[1] for line in examples.splitlines() if line.startswith("* `")]


def test_documented_examples_can_be_calculated():
    formulas = documented_example_formulas()
    assert len(formulas) > 60

    for formula in formulas:
        result = main(
            formula=formula,
            **{
                name: with_metadata(timeseries(0.5, 4.0, 16.0, -9.0), {"max": 10.0, "min": -5.0})
                for name in SERIES_INPUT_NAMES
            },
        )["result"]
        # e.g. a.resample("1D").sum() has fewer points in time, and a.reindex(...) all 24 hours
        # of the queried day
        assert 1 <= len(result) <= 24, formula


A = (4.0, 16.0, 2.5, -2.5)
B = (2.0, 8.0, 0.0, 1.0)
C = (1.0, -1.0, 0.0, 1.0)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("(a + b) / 2", [3.0, 12.0, 1.25, -0.75]),
        ("=a-b", [2.0, 8.0, 2.5, -3.5]),
        ("a * b / 2", [4.0, 64.0, 0.0, -1.25]),
        ("a / b", [2.0, 2.0, np.inf, -2.5]),
        ("a % 3", [1.0, 1.0, 2.5, 0.5]),
        ("a * 19 / 100", [0.76, 3.04, 0.475, -0.475]),
        ("a**2", [16.0, 256.0, 6.25, 6.25]),
        ("a**-1", [0.25, 0.0625, 0.4, -0.4]),
        ("sqrt(a)", [2.0, 4.0, np.sqrt(2.5), np.nan]),
        ("a**(1/b)", [2.0, np.sqrt(2.0), np.inf, -2.5]),
        ("log(a)", [np.log(4.0), np.log(16.0), np.log(2.5), np.nan]),
        ("log10(a * 25)", [2.0, np.log10(400.0), np.log10(62.5), np.nan]),
        ("log(a) / log(2)", [2.0, 4.0, np.log2(2.5), np.nan]),
        ("exp(1) * b", [2 * np.e, 8 * np.e, 0.0, np.e]),
        ("abs(a)", [4.0, 16.0, 2.5, 2.5]),
        ("floor(a)", [4.0, 16.0, 2.0, -3.0]),
        ("ceil(a)", [4.0, 16.0, 3.0, -2.0]),
        ("floor(a + 0.5)", [4.0, 16.0, 3.0, -2.0]),
        ("floor(a / 3 * 100 + 0.5) / 100", [1.33, 5.33, 0.83, -0.83]),
        ("sin(b * 45 * pi / 180)", [1.0, 0.0, 0.0, np.sqrt(0.5)]),
        (
            "arctan2(b, a) * 180 / pi",
            [np.degrees(np.arctan2(b, a)) for a, b in zip(A, B, strict=True)],
        ),
        ("a > 3", [True, True, False, False]),
        ("2 < a < 10 and b > 1", [True, False, False, False]),
        ("not a > 3 or b == 8", [False, True, True, True]),
        ("(c > 0) * a + (c <= 0) * b", [4.0, 8.0, 0.0, -2.5]),
        ("(a + b + abs(a - b)) / 2", [4.0, 16.0, 2.5, 1.0]),
        ("(a + b - abs(a - b)) / 2", [2.0, 8.0, 0.0, -2.5]),
        # pandas eval calculates & and | after comparisons, unlike Python
        ("a > 3 & b > 1", [True, True, False, False]),
        # e.g. copied from a text with line breaks
        ("(a +\n b) / 2\n", [3.0, 12.0, 1.25, -0.75]),
        ("a - a.mean()", [-1.0, 11.0, -2.5, -7.5]),
        ("(a - a.mean()) / a.std()", [(x - 5.0) / np.std(A, ddof=1) for x in A]),
        ("a.round()", [4.0, 16.0, 2.0, -2.0]),
        ("a.diff()", [np.nan, 12.0, -13.5, -5.0]),
        ("a.rolling(2).mean()", [np.nan, 10.0, 9.25, 0.0]),
        ('a.rolling("2h").max()', [4.0, 16.0, 16.0, 2.5]),
        ("a.where(c > 0, b)", [4.0, 8.0, 0.0, -2.5]),
        ("a.clip(lower=b)", [4.0, 16.0, 2.5, 1.0]),
        ("abcde.mean(axis=1)", [7.0 / 3, 23.0 / 3, 2.5 / 3, -0.5 / 3]),
        ("abcde.std(axis=1)", [np.std(values, ddof=1) for values in zip(A, B, C, strict=True)]),
        ('abcde["b"] + abcde.max(axis=1)', [6.0, 24.0, 2.5, 2.0]),
        ("np.sign(a)", [1.0, 1.0, 1.0, -1.0]),
        ("np.maximum(a, b)", [4.0, 16.0, 2.5, 1.0]),
        ('a.groupby(pd.Grouper(freq="2h")).cumsum()', [4.0, 20.0, 2.5, 0.0]),
    ],
)
def test_formulas(formula, expected):
    result = main(formula=formula, a=timeseries(*A), b=timeseries(*B), c=timeseries(*C))["result"]

    pd.testing.assert_series_equal(
        result, pd.Series(expected, index=timeseries(*A).index), check_dtype=False
    )


def test_unused_inputs_are_ignored():
    result = main(formula="a * 2", a=timeseries(1.0), b=pd.Series(["no number"]))["result"]

    assert result.tolist() == [2.0]


def test_inputs_are_calculated_as_floating_point_numbers():
    a = pd.Series([1, 2, 4], index=timeseries(0, 0, 0).index)
    b = pd.Series([True, False, True], index=a.index)

    assert main(formula="a**-1", a=a)["result"].tolist() == [1.0, 0.5, 0.25]
    assert main(formula="a % 0", a=a)["result"].isna().all()
    assert main(formula="a * b", a=a, b=b)["result"].tolist() == [1.0, 0.0, 4.0]


def test_values_are_combined_at_the_same_points_in_time():
    a = timeseries(1.0, 2.0, 3.0)
    b = timeseries(10.0, 20.0, 30.0, 40.0).iloc[1:]

    result = main(formula="a + b", a=a, b=b)["result"]

    pd.testing.assert_series_equal(result, timeseries(np.nan, 22.0, 33.0, np.nan))


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("a + b", [np.nan, 22.0, np.nan, np.nan]),
        ("a.add(b, fill_value=0)", [1.0, 22.0, np.nan, 40.0]),
        ("a.sub(b, fill_value=0)", [1.0, -18.0, np.nan, -40.0]),
        ("abcde.sum(axis=1, min_count=1)", [1.0, 22.0, np.nan, 40.0]),
        ("abcde.sum(axis=1)", [1.0, 22.0, 0.0, 40.0]),
    ],
)
def test_missing_values_can_count_as_zero(formula, expected):
    a = timeseries(1.0, 2.0, np.nan)
    b = timeseries(10.0, 20.0, np.nan, 40.0).iloc[1:]

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = main(formula=formula, a=a, b=b)["result"]

    pd.testing.assert_series_equal(result, timeseries(*expected), check_freq=False)


@pytest.mark.parametrize(
    "formula",
    [
        "a.add(b, fill_value=0)",
        "abcde.sum(axis=1, min_count=1)",
        'a.resample("1h").mean().add(b.resample("1h").mean(), fill_value=0)',
        'abcde.resample("1h").mean().sum(axis=1, min_count=1)',
    ],
)
def test_missing_values_count_as_zero_also_if_b_has_no_values(formula):
    a = timeseries(1.0, 2.0, 3.0)
    b = timeseries()

    result = main(formula=formula, a=a, b=b)["result"]

    pd.testing.assert_series_equal(result, a, check_freq=False)


def values_at_minutes(values_by_minute):
    start = timeseries(0.0).index[0]
    return pd.Series(
        list(values_by_minute.values()),
        index=pd.DatetimeIndex([start + pd.Timedelta(minutes=m) for m in values_by_minute]),
        dtype="float64",
    )


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ('a.resample("1h").mean() + b.resample("1h").mean()', [17.0, np.nan, np.nan]),
        ('a.resample("1h").mean().add(b.resample("1h").mean(), fill_value=0)', [17.0, 40.0, 5.0]),
        ('abcde.resample("1h").mean().sum(axis=1, min_count=1)', [17.0, 40.0, 5.0]),
    ],
)
def test_timeseries_with_different_points_in_time_can_be_aggregated_first(formula, expected):
    # a has no value after 02:00 and b none in the hour from 01:00 to 02:00
    a = values_at_minutes({5: 10.0, 25: 20.0, 65: 40.0})
    b = values_at_minutes({10: 1.0, 50: 3.0, 150: 5.0})

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = main(formula=formula, a=a, b=b)["result"]

    pd.testing.assert_series_equal(result, timeseries(*expected), check_freq=False)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [("1 / a", [np.inf, -1.0]), ("sqrt(a)", [0.0, np.nan]), ("log(a)", [-np.inf, np.nan])],
)
def test_impossible_calculations_do_not_stop_the_calculation(formula, expected):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = main(formula=formula, a=timeseries(0.0, -1.0))["result"]

    pd.testing.assert_series_equal(result, timeseries(*expected))


def utc_timeseries_around_start_of_daylight_saving_time():
    """1.0 every 2 hours from 20:00 UTC on 2026-03-28 to 00:00 UTC on 2026-03-30

    2026-03-29 has 23 hours in German time, from 23:00 UTC on 2026-03-28 to 22:00 UTC.
    """
    return pd.Series(
        1.0, index=pd.date_range("2026-03-28T20:00:00Z", "2026-03-30T00:00:00Z", freq="2h")
    )


def with_time_zone(series, time_zone):
    """The series with metadata specifying the time zone it should be evaluated in"""
    series = with_metadata(series, {})
    series.attrs["dataset_metadata"]["default_timezone"] = time_zone
    return series


@pytest.mark.parametrize(
    ("time_zone", "formula"),
    [
        ("Europe/Berlin", 'a.groupby(pd.Grouper(freq="D")).cumsum()'),
        (
            None,
            'a.tz_convert("Europe/Berlin").groupby(pd.Grouper(freq="D")).cumsum().tz_convert("UTC")',
        ),
        (None, 'modify_timezone(a, "Europe/Berlin").groupby(pd.Grouper(freq="D")).cumsum()'),
        ("UTC", 'modify_timezone(a, "Europe/Berlin").groupby(pd.Grouper(freq="D")).cumsum()'),
    ],
)
def test_running_totals_can_start_again_at_midnight_in_german_time(time_zone, formula):
    a = utc_timeseries_around_start_of_daylight_saving_time()
    if time_zone is not None:
        a = with_time_zone(a, time_zone)

    result = main(formula=formula, a=a)["result"]

    pd.testing.assert_series_equal(
        result,
        pd.Series(
            [1.0, 2.0, *range(1, 12), 1.0, 2.0],
            index=utc_timeseries_around_start_of_daylight_saving_time().index,
            dtype="float64",
        ),
        check_freq=False,
    )


BERLIN_DAYS = ("Europe/Berlin", [2.0, 11.0, 2.0])
UTC_DAYS = ("UTC", [2.0, 12.0, 1.0])
# daylight saving time started on 2026-03-08 in New York, so days start at 04:00 UTC
NEW_YORK_DAYS = ("America/New_York", [4.0, 11.0])


@pytest.mark.parametrize(
    ("time_zones", "formula", "days"),
    [
        # the time zone of the metadata
        (["Europe/Berlin"], 'a.resample("1D").sum()', BERLIN_DAYS),
        (["America/New_York"], 'a.resample("1D").sum()', NEW_YORK_DAYS),
        (["UTC"], 'a.resample("1D").sum()', UTC_DAYS),
        ([None], 'a.resample("1D").sum()', UTC_DAYS),
        (["Europe/Berlin", "Europe/Berlin"], '(a + b).resample("1D").sum() / 2', BERLIN_DAYS),
        (["Europe/Berlin", "Europe/Berlin"], 'abcde.resample("1D").sum().a', BERLIN_DAYS),
        # inputs without metadata do not count
        (["Europe/Berlin", None], '(a + b).resample("1D").sum() / 2', BERLIN_DAYS),
        ([None, "Europe/Berlin"], 'abcde.resample("1D").sum().a', BERLIN_DAYS),
        # different time zones
        (["Europe/Berlin", "America/New_York"], '(a + b).resample("1D").sum() / 2', UTC_DAYS),
        (["Europe/Berlin", "America/New_York"], 'abcde.resample("1D").sum().a', UTC_DAYS),
        # unused inputs do not count
        (["Europe/Berlin", "America/New_York"], 'a.resample("1D").sum()', BERLIN_DAYS),
        (["Europe/Berlin", "America/New_York"], 'a.resample("1D").sum() + meta.b.max', BERLIN_DAYS),
        # other time zones in the formula
        (["UTC"], 'modify_timezone(a, "Europe/Berlin").resample("1D").sum()', BERLIN_DAYS),
        ([None], 'modify_timezone(a, "Europe/Berlin").resample("1D").sum()', BERLIN_DAYS),
        (["Europe/Berlin"], 'modify_timezone(a, "UTC").resample("1D").sum()', UTC_DAYS),
    ],
)
def test_days_are_days_in_the_time_zone_of_the_metadata(time_zones, formula, days):
    inputs = {
        name: utc_timeseries_around_start_of_daylight_saving_time()
        for name in SERIES_INPUT_NAMES[: len(time_zones)]
    }
    for (name, series), time_zone in zip(inputs.items(), time_zones, strict=True):
        if time_zone is not None:
            inputs[name] = with_time_zone(series, time_zone)
            series.attrs["metrics"][0]["inherited"] = {"max": 0.0}

    result = main(formula=formula, **inputs)["result"]

    time_zone, expected = days
    pd.testing.assert_series_equal(
        result,
        pd.Series(
            expected,
            index=pd.date_range(
                pd.Timestamp("2026-03-28T20:00:00Z").tz_convert(time_zone).normalize(),
                periods=len(expected),
                freq="D",
            ).tz_convert("UTC"),
        ),
        check_freq=False,
        check_names=False,
    )


@pytest.mark.parametrize(
    ("time_zone_from_metadata", "formula", "days"),
    [
        (True, 'a.resample("1D").sum()', BERLIN_DAYS),
        (False, 'a.resample("1D").sum()', UTC_DAYS),
        (False, '(a + b).resample("1D").sum() / 2', UTC_DAYS),
        (False, 'abcde.resample("1D").sum().a', UTC_DAYS),
        (False, 'modify_timezone(a, "Europe/Berlin").resample("1D").sum()', BERLIN_DAYS),
    ],
)
def test_time_zone_from_metadata_can_be_switched_off(time_zone_from_metadata, formula, days):
    a, b = (
        with_time_zone(utc_timeseries_around_start_of_daylight_saving_time(), "Europe/Berlin")
        for _ in range(2)
    )

    result = main(formula=formula, a=a, b=b, time_zone_from_metadata=time_zone_from_metadata)[
        "result"
    ]

    time_zone, expected = days
    pd.testing.assert_series_equal(
        result,
        pd.Series(
            expected,
            index=pd.date_range(
                pd.Timestamp("2026-03-28T20:00:00Z").tz_convert(time_zone).normalize(),
                periods=len(expected),
                freq="D",
            ).tz_convert("UTC"),
        ),
        check_freq=False,
        check_names=False,
    )


def test_inputs_without_time_zone_are_not_converted():
    a = with_time_zone(timeseries(1.0, 2.0).tz_localize(None), "Europe/Berlin")

    result = main(formula='a.resample("1D").sum()', a=a)["result"]

    pd.testing.assert_series_equal(
        result, pd.Series([3.0], index=pd.DatetimeIndex(["2026-01-01"])), check_freq=False
    )


def test_points_in_time_without_time_zone_are_taken_as_german_time():
    # 00:30 and 23:30 in German time are on the same day, unlike 00:30 and 23:30 in UTC
    a = pd.Series(
        [1.0, 2.0], index=pd.DatetimeIndex(["2026-01-01T00:30:00", "2026-01-01T23:30:00"])
    )

    result = main(formula='modify_timezone(a, "Europe/Berlin").resample("1D").sum()', a=a)["result"]

    pd.testing.assert_series_equal(
        result,
        pd.Series(
            [3.0],
            index=pd.date_range("2026-01-01", periods=1, tz="Europe/Berlin").tz_convert("UTC"),
        ),
        check_freq=False,
    )


@pytest.mark.parametrize(
    "formula",
    [
        'modify_timezone(a, "Europe/Berlin")',
        'a.tz_convert("Asia/Kolkata") * 2',
        'modify_timezone(a, "Europe/Berlin") + b',
    ],
)
def test_result_is_in_utc(formula):
    a = timeseries(1.0, 2.0)
    b = timeseries(0.0, 0.0)

    result = main(formula=formula, a=a, b=b)["result"]

    assert str(result.index.tz) == "UTC"
    pd.testing.assert_series_equal(
        result, a * (2 if "* 2" in formula else 1), check_freq=False, check_names=False
    )


def test_result_without_time_zone_stays_without_time_zone():
    a = timeseries(1.0, 2.0).tz_localize(None)

    result = main(formula="a * 2", a=a)["result"]

    pd.testing.assert_series_equal(result, a * 2)


def test_result_has_neither_name_nor_metadata():
    a = timeseries(1.0, 2.0).rename("level")
    a.attrs = {"metrics": [{"id": "level", "value_dimensions": [{"unit": "m"}]}]}

    result = main(formula="a * 100", a=a)["result"]

    assert result.name is None
    assert result.attrs == {}
    assert a.attrs != {}


@pytest.mark.parametrize(
    ("formula", "invalid_input", "message_part"),
    [
        ("", "formula", "enter a formula"),
        (" = ", "formula", "enter a formula"),
        ("(a + b", "formula", "brackets"),
        ("2a", "formula", "2 * a"),
        ("a * 19%", "formula", "/ 100"),
        ("a <> b", "formula", "!="),
        ("a = b", "formula", "=="),
        ("a^2", "formula", "a**2"),
        ("a * 1,5", "formula", "1.5"),
        ("c * 2", "c", "no timeseries connected to the input c"),
        ("e * a", "e", "exp(1)"),
        ("A + B", "formula", "a instead of A"),
        ("a + x", "formula", "x is unknown"),
        ("a * sqrt", "formula", "sqrt(a)"),
        ("SQRT(a)", "formula", "sqrt(a)"),
        ("WURZEL(a)", "formula", "sqrt(a)"),
        ("LN(a)", "formula", "log(a)"),
        ("LOG(a)", "formula", "log10(a)"),
        ("ROUND(a, 2)", "formula", "a.round(2)"),
        ("MAX(a, b)", "formula", "abcde.max(axis=1)"),
        ("PI()", "formula", "Write for example pi instead"),
        ("ATAN2(a, b)", "formula", "arctan2(b, a)"),
        ("quadrat(a)", "formula", "Available functions: sqrt,"),
        ("MEDIAN(a, b)", "formula", "abcde.median(axis=1)"),
        ("IF(c > 0, a, b)", "formula", "a.where(c > 0, b)"),
        ("log(a, 2)", "formula", "log(a) / log(2)"),
        ("sqrt(1,5)", "formula", "1.5"),
        ("arctan2(a)", "formula", "two values"),
        ("a(b + 1)", "formula", "a * (b + c)"),
        ("2(a + 1)", "formula", "a * (b + c)"),
        ("a.mean()", "formula", "does not calculate a timeseries"),
        ("abcde * 2", "formula", "does not calculate a timeseries"),
        ("2 + 3", "formula", "does not calculate a timeseries"),
        ("a.Mean()", "formula", "could not be calculated: 'Series' object has no attribute"),
        ('a.rolling("one hour").mean()', "formula", "could not be calculated"),
        ("a.where(x > 0)", "formula", "x is unknown"),
        ("a + x", "formula", "pandas as pd, numpy as np and hdhelpers."),
        ("quadrat(a)", "formula", ", arctan2, modify_timezone."),
        ("pd(a)", "formula", "The function pd does not exist here."),
        ('modify_timezone(a, "Mars/Olympus")', "formula", "could not be calculated"),
    ],
)
def test_errors_explain_what_to_change(formula, invalid_input, message_part):
    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(formula=formula, a=timeseries(1.0), b=timeseries(2.0), d=timeseries(3.0))

    assert exc_info.value.extra_information["invalid_component_inputs"] == [invalid_input]
    assert message_part in str(exc_info.value)


def test_abcde_contains_all_connected_inputs():
    a = timeseries(1.0, 2.0, 3.0)
    d = timeseries(10.0, 20.0, 30.0, 40.0).iloc[1:]

    result = main(formula="abcde.count(axis=1) + abcde.sum(axis=1)", a=a, d=d)["result"]

    pd.testing.assert_series_equal(result, timeseries(2.0, 24.0, 35.0, 41.0))


def test_abcde_needs_a_connected_input():
    with pytest.raises(ComponentInputValidationException, match="abcde"):
        main(formula="abcde.mean(axis=1)")


def test_values_which_are_not_numbers():
    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(formula="a + b", a=timeseries(1.0), b=pd.Series(["no number"]))

    assert exc_info.value.extra_information["invalid_component_inputs"] == ["b"]


def with_metadata(series, inherited):
    """The series with metadata following the conventions, in their JSON form"""
    series.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "level",
            "queried_metrics": ["level"],
            "ref_interval_start_timestamp": "2026-01-01T00:00:00+00:00",
            "ref_interval_end_timestamp": "2026-01-02T00:00:00+00:00",
            "ref_interval_type": "right_open",
            "ref_data_frequency": "1h",
            "default_timezone": "Europe/Berlin",
        },
        "metrics": [
            {
                "id": "level",
                "name": "Water level",
                "value_dimensions": [
                    {"column": "value", "unit": "m", "measurement": "level", "decimals": 1}
                ],
                "inherited": inherited,
            }
        ],
    }
    return series


PROPERTIES = {
    "max": 20.0,
    "min": -10.0,
    "upper limit": 15.0,
    "unit": "km",
    "description": "Plant North",
    "site": "North",
}


@pytest.mark.parametrize("attached", [False, True])
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("a > meta.a.max", [False, True, False]),
        ("a.where(a <= meta.a.max)", [12.34, np.nan, -20.0]),
        ("a.clip(lower=meta.a.min, upper=meta.a.max)", [12.34, 20.0, -10.0]),
        ('a.where(a <= meta.a["upper limit"])', [12.34, np.nan, -20.0]),
        ('a - meta.a["max"]', [-7.66, 10.0, -40.0]),
        ("a.round(meta.a.decimals)", [12.3, 30.0, -20.0]),
        ("a.resample(meta.a.data_frequency).sum()", [12.34, 30.0, -20.0]),
        ('a.resample("1D").agg(meta.a.default_aggregation_method.lower())', [22.34 / 3]),
        # the inputs keep their metadata for the functions of hdhelpers
        ('a > hdhelpers.metadata.get_series_info(a, "max")', [False, True, False]),
        ('a - hdhelpers.metadata.get_series_info(a, "upper limit")', [-2.66, 15.0, -35.0]),
        (
            'a.resample("1D").agg(hdhelpers.metadata.get_series_default_aggregation_method(a).lower())',
            [22.34 / 3],
        ),
        (
            (
                "a.reindex(pd.date_range(hdhelpers.metadata.get_queried_interval(a)[0],"
                " hdhelpers.metadata.get_queried_interval(a)[1], freq=meta.a.data_frequency,"
                ' inclusive="left"))'
            ),
            [12.34, 30.0, -20.0] + [np.nan] * 21,
        ),
    ],
)
def test_metadata_can_be_used(formula, expected, attached):
    a = with_metadata(timeseries(12.34, 30.0, -20.0), PROPERTIES)
    if attached:
        # like the runtime does for workflow inputs
        attach_metadata(a, "SERIES")

    result = main(formula=formula, a=a)["result"]

    np.testing.assert_allclose(result.to_numpy(dtype="float64"), expected)
    assert result.attrs == {}


def test_metadata_fields_are_looked_up_as_specified_by_the_conventions():
    a = with_metadata(timeseries(1.0), PROPERTIES)

    # fields of the conventions describing the timeseries itself are not inherited
    assert metadata_value(a, "unit") == "m"
    assert metadata_value(a, "description") is None
    assert metadata_value(a, "name") == "Water level"
    assert metadata_value(a, "site") == "North"
    # fallbacks to the dataset metadata
    assert metadata_value(a, "data_frequency") == "1h"
    assert metadata_value(a, "default_timezone") == "Europe/Berlin"


@pytest.mark.parametrize(
    ("formula", "invalid_input", "message_part"),
    [
        ("a > meta", "formula", "meta is followed by the input"),
        ("a > meta.x.max", "formula", "meta is followed by the input"),
        ('a > meta["a"].max', "formula", "meta is followed by the input"),
        ("a > meta.a", "formula", "meta.a is followed by the field"),
        ("a > meta.c.max", "c", "no timeseries connected to the input c"),
        (
            "a > meta.a.Max",
            "formula",
            (
                "The metadata of a contain no field Max. Available fields: column, data_frequency,"
                " decimals, default_aggregation_method, default_timezone, id, max, measurement,"
                " name, unit."
            ),
        ),
        ('a > meta.a["upper limit"]', "formula", "contain no field upper limit"),
        ("a > meta.b.max", "b", "The timeseries connected to the input b has no metadata"),
    ],
)
def test_metadata_errors_explain_what_to_change(formula, invalid_input, message_part):
    a = with_metadata(timeseries(1.0), {"max": 2.0})

    with pytest.raises(ComponentInputValidationException) as exc_info:
        main(formula=formula, a=a, b=timeseries(1.0))

    assert exc_info.value.extra_information["invalid_component_inputs"] == [invalid_input]
    assert message_part in str(exc_info.value)
