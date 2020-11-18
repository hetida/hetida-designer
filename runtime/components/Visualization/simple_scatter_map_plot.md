# Simple Scatter Map Plot

## Description
This component marks locations on a map.

## Inputs
* **data** (Pandas DataFrame): Must have 
 * "lat" and a "lon" columns containing latitude and longitude coordinates
 * "name" column where the titles of the hovering rectangle are obtained from.
 * "description" column where additional information is stored that is included in the hovering rectangles.
 * A column of which the name is equal to the value provided in **cat_color_col** input. This must be a categorical column, e.g. String values like `"A", "B", ...`.
* **color_map** (Any): Must be a dictionary providing color values for the category values in `data[cat_color_col]`, e.g. `{"A": "#005099", "B": "#6633FF"}`
* **cat_color_col** (String): The name of the column containing the categories in **data**.

## Outputs
* **map_plot** (Plotly Json): The generated Plotly Json map plot. This is used by the hetida designer frontend for plotting the results.

## Details
This is an example for a Scatter Map plot. It draws an Openstreetmap map, marking all locations in **data** with a small circle.

## Examples
The json input of a typical call of this component is
```
{
    "cat_color_col": "Organisation",
    "color_map": {
        "Folkwang": "#005099",
        "von der Heydt": "#00925B",
        "lehmbruck": "#0076BD"
    },
    "data": {
        "lat": [
            51.442666,
            51.256625,
            51.430145
        ],
        "lon": [
            7.005126,
            7.146598,
            6.765380
        ],
        "name": [
            "Folkwang Museum Essen",
            "Von der Heydt Museum Wuppertal",
            "Lehmbruck Museum Duisburg"
        ],
        "description": [
            "",
            "",
            ""
        ],
        "Organisation": [
            "Folkwang",
            "von der Heydt",
            "lehmbruck"
        ]
    }
}
```
