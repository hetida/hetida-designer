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
