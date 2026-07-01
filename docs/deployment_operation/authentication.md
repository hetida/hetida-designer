# OpenID Connect Authentication

Hetida designer supports authentication via the OpenID Connect standard using the Auth Code flow with PKCE for the frontend.

Authentication has to be enabled in at least both the backend and the frontend. We recommend to also activate it for the runtime as well, even if not exposed and only accessed internally.

Additionaly you can configure how outgoing internal (i.e. between backend and runtime) or outgoing external requests (i.e. to adapters) are authenticated.

You will need an OpenID provider, for example [keycloak](https://www.keycloak.org/), which is used here for demonstration purposes.

## Setup

Save a copy of the `docker-compose-dev.yml` with the new name `docker-compose-keycloak.yml`, modify the **hetida-designer-frontend**, the **hetida-designer-backend** and the **hetida-designer-runtime** service and add a **keycloak** service as follows:

```yaml
...

  hetida-designer-frontend:
    ...
    volumes:
      - ./hetida_designer_config_keycloak.json:/usr/share/nginx/html/assets/hetida_designer_config.json
...

  hetida-designer-backend:
    ...
    environment:
      ...
      - HD_USE_AUTH=true
      ...
    ...
...
  hetida-designer-runtime:
    ...
    environment:
      ...
      HD_USE_AUTH: "true"
      ...
    ...
...

  hetida-designer-keycloak:
    image: quay.io/keycloak/keycloak:25.0.1
    ports:
      - 8081:8080
    environment:
      - KEYCLOAK_ADMIN=admin
      - KEYCLOAK_ADMIN_PASSWORD=admin
    volumes:
      - ./hetida-designer-realm.json:/opt/keycloak/data/import/hetida-designer-realm.json
    command:
      - start-dev
      - --import-realm

...

```

In order to enable OpenID Connect in the frontend, create a `hetida_designer_config_keycloak.json` file as follows and mount it into the `hetida-designer-web` service (see docker-compose file above):

```json
{
  "apiEndpoint": "/hdapi",
  "userInfoText": "",
  "authEnabled": true,
  "authConfig": {
    "authority": "http://localhost:8081/realms/hetida-designer",
    "clientId": "hetida-designer",
    "userNameAttribute": "preferred_username",
    "renewTimeBeforeTokenExpiresInSeconds": 10
  }
}
```

Details:

* `authority` and `clientId` have to be provided in order for the login to work.
* `userNameAttribute` is the name of the attribute in the id token which contains the username (required to display the username in the UI).
* `renewTimeBeforeTokenExpiresInSeconds` controls how long before expiration the access token is automatically renewed (token refresh).

For more configuration options see https://github.com/damienbod/angular-auth-oidc-client.

Our setup uses a pre-configured keycloak realm named `hetida-designer` which is imported from `hetida-designer-realm.json` and has an example user with the following credentials:

* username: `testuser`
* password: `testpassword`

!!! warning
    You should not use this demonstration setup in a production environment. Make sure you use sensible security defaults and secure credentials when configuring your OpenID provider.

Once the user is logged in, the hetida designer frontend will add the access token to all REST requests (as a bearer token in the HTTP Authorization header), i.e. to the backend but also to adapter webservices.

Using the default settings, backend and runtime will use the access token when making requests against each other or against configured adapters. See below for more options for outgoing requests.

## Enabling Authentication for adapters
As explained above, hetida designer backend/runtime will by default (`HD_EXTERNAL_AUTH_MODE` is set to `FORWARD_OR_FIXED`) forward any bearer access token when making http requests to adapter webservices, if the respective environment variables `HD_USE_AUTH` are set to `true`.

It is then up to you as the author of a [custom adapter](../integration_guide/adapter_system/custom_adapters/) to configure/enable auth checking in your adapter webservice code.

See below for more configuration options for outgoing external requests.

## Export/Import against protected backend
In order to make the included scripts for exporting/importing work against a backend with enabled auth, you can provide a valid Bearer token directly when using the backend/runtime image for invoking scripts (like export/import). You have to set

* The environment variable `HD_USE_AUTH` to `true` for your script invocation
* The environment variable `HD_EXTERNAL_AUTH_MODE` to `FORWARD_OR_FIXED` (the default)
* The environment variable `HD_BEARER_TOKEN_FOR_OUTGOING_REQUESTS` to contain the Bearer token that should be used.


## Outgoing authentication configuration for runtime/backend
By *outgoing* we mean http requests made from runtime or backend, for example to each other or to adapters.

### Outgoing Internal http Requests
hetida designer backend/runtime are using internal http requests between each other when run as separate services.

You can configure how these internal requests are equipped with valid bearer access tokens using the `HD_INTERNAL_AUTH_MODE` environment variable. It supports the following values:

* `OFF` : internal requests will not be equipped with an Authorisation header.
* `FORWARD_OR_FIXED` (default): If the outgoing request is made during handling of a web request which came with a bearer token, this token will be forwarded. Make sure that token duration is long enough in particular when running long lasting workflow executions. If there is no request context then this mode will fall back to sending the 'fixed' access token provided via the `HD_BEARER_TOKEN_FOR_OUTGOING_REQUESTS` environment variable. If that isn't present, no Authorization header will be send.
* `CLIENT` : The service handles access token management by authenticating itself via a client credential grant against the auth provider. The relevant connection and credential information is expected in the `HD_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS` environment variable. It must contain a json-encoded string specifying a ServiceCredentials object, for example:
```
{"realm": "my-realm", "auth_url": "https://test.com", "audience": "account", "grant_credentials": {"grant_type": "client_credentials", "client_id": "my-client",  "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false}, "post_kwargs": {}}
```
See the [config.py](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun/webservice/config.py) file or the [auth_outgoing.py](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun/webservice/auth_outgoing.py) file in this repository for further details.

### Scheduling
Scheduling has its own internal auth mode `HD_SCHEDULING_INTERNAL_AUTH_MODE` which can be either `OFF` or `CLIENT`. There is no `FORWARD_OR_FIXED` since schedule executions are not triggered by (user) events. If set to `CLIENT` it expects `HD_SCHEDULING_INTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS` to contain client service credentials that are used when accessing the runtime while running scheduled jobs.

!!! warning
    Note, that since all users are allowed to create and edit schedules, they effectively can perform actions with the rights / authority of these service credentials. This may elevate the user's privileges if the service user has more rights.

### Outgoing External http Requests
hetida designer runtime is making external http requests when communicating with adapters or when used for exporting/importing components/workflows from another designer instance (scripting).

You can configure how these external requests are equipped with valid access tokens using the `HD_EXTERNAL_AUTH_MODE` environment variable. It supports the following values:

* `OFF` : external requests will not be equipped with an Authorisation header.
* `FORWARD_OR_FIXED` (default): If the outgoing request is made during handling of a web request which came with a bearer token, it will forward this bearer token. Make sure that token duration is long enough in particular when reading/writing a lot of data from adapters! If there is no request context, e.g. when using the backend or runtime for exporting/importing (i.e. scripting), then this mode will fall back to sending the access token provided via the `HD_BEARER_TOKEN_FOR_OUTGOING_REQUESTS` environment variable. If that isn't present, no Authorization header will be send.
* `CLIENT` : The service handles access token management by authenticating itself via a client credential grant against the auth provider. The relevant connection and credential information is expected in the `HD_EXTERNAL_AUTH_CLIENT_SERVICE_CREDENTIALS` environment variable. It must contain a json-encoded string specifying a ServiceCredentials object, for example:
```
{"realm": "my-realm", "auth_url": "https://test.com", "audience": "account", "grant_credentials": {"grant_type": "client_credentials", "client_id": "my-client",  "client_secret": "my client secret"}, "post_client_kwargs": {"verify": false}, "post_kwargs": {}}
```
See the [config.py](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun/webservice/config.py) file or the [auth_outgoing.py](https://github.com/hetida/hetida-designer/blob/release/runtime/hetdesrun/webservice/auth_outgoing.py) file in this repository for further details.

### Recommendations
For production setups we recommend to switch both internal and external outgoing authentication mode to `CLIENT` for both backend and runtime. This allows to tailor the service authorization to just the access rights it needs.


## Dashboarding
In addition to the auth configuration described above you need to specify how the dashboard frontend can reach the auth provider (like keycloak) via setting the backend's `HD_DASHBOARDING_FRONTEND_AUTH_SETTINGS` environment variable to a json object: The default setup working with the setup described above is:

```
{ 
    "auth_url" : "http://localhost:8081/",
    "client_id": "hetida-designer",
    "realm": "hetida-designer"
}
```