# Time to length

## Description
Converts time related data to length related data.

## Inputs
* **data** (Pandas Series): Indices must be datetimes.
* **speed** (Integer, Float or Pandas Series): For speed being Pandas Series, indices must be datetimes and entries must be numeric.  

## Outputs
* **result** (Pandas Series): The length related data.

## Details
The component interprets the values of speed as speed in m/s with linear rise between the the given indices. It calculates the covered distance by speed and matches the result with the values given by data.

If the indices of data and speed are different, result is a conclusion of the insersection of both indices. Therefore, the covered distances will be calculated as exact as speed suffers and after that the corresponding distances and values of data will be matched.

Multiple indices in the result are possible.


## Examples
The json input of a typical call of this component with speed as Pandas Series is
```
{
	"data": {
				"2019-08-01T15:20:12": 5.0,
            	"2019-08-01T15:20:14": 8.2,
            	"2019-08-01T15:20:15": 9.3,
				"2019-08-01T15:20:17": 8.6, 
				"2019-08-01T15:20:18": 0.8, 
				"2019-08-01T15:20:21": 3.4, 
            	"2019-08-01T15:20:25": 2.1
	},
	"speed": {
				"2019-08-01T15:20:12": 1,
            	"2019-08-01T15:20:14": 2,
            	"2019-08-01T15:20:15": 3,
				"2019-08-01T15:20:17": 2, 
				"2019-08-01T15:20:18": 0, 
				"2019-08-01T15:20:21": 0, 
            	"2019-08-01T15:20:25": 4   
	}
}
```
The expected output is
```
	"result": {
				0.0: 5.0,
            	3.0: 8.2,
            	5.5: 9.3,
				10.5: 8.6, 
				11.5: 0.8, 
				11.5: 3.4, 
            	19.5: 2.1
	}

```

The json input of a typical call of this component with speed as Integer is
```
{
	"data": {
				"2019-08-01T15:20:12": 1.2,
             	"2019-08-01T15:20:14": 7.2,
             	"2019-08-01T15:20:15": 0.3,
             	"2019-08-01T15:20:20": 0.5,
	},
    "speed": 5
	}
}
```
The expected output is
```
	"result": {
				0.0:     1.2
 				10.0:    7.2
 				15.0:    0.3
 				40.0:    0.5  
	}
```
