# Experimental Dashboarding
hetida designer workflow/component execution can generate outputs containing plotly json objects, which in turn can be rendered using plotly.js. One actually quite common use case for hetida designer is to use it as a backend service for providing highly customized analytical plots written in Python using Plotly to specialized frontends.

hetida designer provides an experimental (read: proof of concept / demo!) dashboard view for each component/workflow to demonstrate these capabilities. I.e. to each component / workflow a dashboard exists that is tied to the current test wiring in the execution dialog.

![Example Dashboard for the Visualization Demo workflow](./assets/dashboard.png)

Notes:
* In practice you would set the wiring directly in your web application's front- or backend and call the execution endpoint.
* The dashboard here is provided as pure html with inline styles containing pure javascript while loading additional js libraries and CSS from external CDNs. In a real use case you would of course use a modern frontend framework with plotly wrapper components and accompanying build system and so on.

## Basics
The dashboard is currently backend-generated and reachable via the url:

```
URL_TO_BACKEND-API/transformations/<id>/dashboard
```
The id is the corresponding transformation revision id which you can find in the "Edit Details" dialog of a component / workflow. E.g. http://localhost/hdapi/transformations/28120522-a6a5-418f-a658-ab19d5beefe2/dashboard is the url of the multitsframe plot component's dashboard when working with the default docker-compose setup.

This link to the dashboard can always be found in the details dialog of your transformation in the frontend:

<img src="./assets/dashboarding_link_in_details_dialog.png" width=400 data-align="center">

## Usage
* The dashboard is tied to the current test wiring which you set in the hd frontend's execution dialog. 
    * In particular you need to execute your component / workflow there at least one time in order for the test wiring to be stored. Before that, the dashboard cannot work.
    * When you change the component/workflow you should do so again to ensure that the dashboard will have a fitting/correct wiring.
* The dashboard shows all plotly outputs of the component / workflow. It (currently) ignores all other outputs!
* You can rearrange the plots by dragging them around using their titlebar or resize them using the resize handles in the bottom corners. The arrangement is saved automatically as part of the test wiring.
* You can set the dashboard to auto-update every X seconds by selecting a value for X in the appropriate selection element in the dashboard user interface.
* You can override all the time ranges of the test wiring with a common absolute or relative time range selectable in the dashboard. 
    * Relative time ranges are practical for autupdating dashboards and combined allow to watch timeseries data progress.
    * Absolute time ranges can be used to depict and share (see below) specific historic data situations with co-workers.
    * Note that time ranges of course only affect those inputs — typically of type SERIES or MULTITSFRAME — which are wired to sources from adapters which actually provide a time range filter. In particular manual input is of course not affected.
* Autoupdate and time-range override settings are stored in the URL. Simply copy that URL if you want to access the dashboard with the same settings later or want to share it with a colleague.

## Authentication
Dashboards require login according to the Backend auth settings (see [auth docs](./enabling_openidconnect_auth.md) for details).

In addition to the configuration described there you need to specify how the dashboard frontend can reach the auth provider (like keycloak) via setting the backend's `HD_DASHBOARDING_FRONTEND_AUTH_SETTINGS` environment variable to a json object: The default setup working with the setup described in the [auth docs](./enabling_openidconnect_auth.md) is

```
{ 
    "auth_url" : "http://localhost:8081/auth/",
    "client_id": "hetida-designer",
    "realm": "hetida-designer"
}
```