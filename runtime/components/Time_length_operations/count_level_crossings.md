# Count level crossings

## Description
This component counts the level crossings of the input data.

## Inputs
* **data** (Pandas Series): Entries must be numeric.
* **level** (Float): Center of the hysteresis-area.
* **hysteresis** (Float): Width of the tolarance window around **level**, must be non-negative. 
* **edge_type** (Float): Input for deciding which type of edges should be counted. Values greater than 0 count ascending level crossings, values smaller than 0 count descending level crossings and equal to 0 all level crossings, respectively.

## Outputs
* **result** (Pandas Series): Series with the number of existing level crossings at the suitable index of data.

## Details
The component counts the level crossings of the given **data**. If the index of data is datetime or numeric, data will be sorted first. 

The input **hysteresis** can be used to define a window of tolerance around the input **level**. For example, if level is 5 and hysteresis is 2, values between 4 and 6 will be tolerated. 

The input **edge_type** defines which kind of level crossings will be counted. Values greater than 0 will count ascending level crossings, values smaller than 0 descending level crossings and the value 0 all level crossings, respectively.
In the given example with edge_type 1, a change from 0 to 10 will be counted as level crossing. If the edge_type is -1, the same change will not be counted.


## Examples
The json input of a typical call of this component, counting all level crossings is
```
{
	"data": {
				"2019-08-01T15:20:00": 1.0,
				"2019-08-01T15:20:10": 7.0,
				"2019-08-01T15:20:20": 5.0,
				"2019-08-01T15:20:30": 4.0,
				"2019-08-01T15:20:40": 2.0,
				"2019-08-01T15:20:50": 5.0,
				"2019-08-01T15:21:00": 1.0,
				"2019-08-01T15:21:10": 8.0,
	},
	"level": 5,
	"hysteresis": 2,
	"edge_type": 0
}
```
The expected output is
```
	"result": {
				"2019-08-01T15:20:00": 0.0,
				"2019-08-01T15:20:10": 1.0,
				"2019-08-01T15:20:20": 1.0,
				"2019-08-01T15:20:30": 1.0,
				"2019-08-01T15:20:40": 2.0,
				"2019-08-01T15:20:50": 2.0,
				"2019-08-01T15:21:00": 2.0,
				"2019-08-01T15:21:10": 3.0,
	}
```

The json input of a call of this component with the same data, counting ascending level crossings is
```
{
	"data": {
				"2019-08-01T15:20:00": 1.0,
				"2019-08-01T15:20:10": 7.0,
				"2019-08-01T15:20:20": 5.0,
				"2019-08-01T15:20:30": 4.0,
				"2019-08-01T15:20:40": 2.0,
				"2019-08-01T15:20:50": 5.0,
				"2019-08-01T15:21:00": 1.0,
				"2019-08-01T15:21:10": 8.0,
	}
	"level": 5
	"hysteresis": 2
	"edge_type": 1
}
```
The expected output is
```
	"result": {
				"2019-08-01T15:20:00": 0.0,
				"2019-08-01T15:20:10": 1.0,
				"2019-08-01T15:20:20": 1.0,
				"2019-08-01T15:20:30": 1.0,
				"2019-08-01T15:20:40": 1.0,
				"2019-08-01T15:20:50": 1.0,
				"2019-08-01T15:21:00": 1.0,
				"2019-08-01T15:21:10": 2.0,
	}
```
