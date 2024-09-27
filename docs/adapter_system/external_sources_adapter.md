# External Sources Adapter
This built-in adapter provides access to some external sources like a weather data API.

## Currently provided external sources

### Open Meteo
We provide sources for [Open Meteo](https://open-meteo.com/) Forecast, Historical Weather, and Historical Forecast APIs.

An open meteo api key can be configured via the `OPEN_METEO_API_KEY` environment variable of the hetida designer runtime. If no API key is provided, the free API is used.

Each source offers a filter in which you can write a json mapping / dictionary of the query parameters of the Open Meteo API call.

Note that multiple values can be specified by passing them as string with `,` as separator. This includes `longitude` and `latitude`. Hetida designer will return a MULTITSFRAME dataframe with extra columns for longitude and latitude. Note that these extra columns are ignored by default by many standard components with a MULTITSFRAME input, for example for visualization. Hence to correctly handle data for multiple locations you may need to write variants / your own components.

Timerange is specified via the explicit time range filter, for example via the respective  control elements in test execution dialog. Therefore any time ranges specified in the query parameter filter are ignored.

Examples for the query parameter filter:
```
{"latitude": 51.4817, "longitude": 7.2165, "hourly": "temperature_2m,precipitation"}
```
or
```
{"latitude": "51.4817,51.45657", "longitude": "7.2165,7.01228", "hourly": "temperature_2m,precipitation", "daily": "temperature"}
```

### Energy-Charts.info API /price endpoint
Energy-Charts.info by Fraunhofer ISE offers data around central european / german energy markets, power usage and distribution.

A source of type MULTITSFRAME is provided for the /price endpoint of the https://energy-charts.info API (https://api.energy-charts.info/#/prices) which makes "dayahead" prices available for selectable bidding zones.

The bidding zone (bzn) is a required filter. See https://api.energy-charts.info/#/prices on documentation about which bidding zone is available und license of the respective data.

Note that there is at the time of writing (2024-09) neither explicit commercial offering for usage of this API nor usage terms restricting usage, at least as far as we know. Please make sure that 

* your usage of this API via hetida designer is in agreement with the current conditions and terms of energy-charts.info!
* your usage of the provided data is in accordance with the provided license.

The source returns a MULTITSFRAME containing a single metric "dayahead-price".


