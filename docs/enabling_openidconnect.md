# Enabling OpenID Connect

This document describes how to enable OpenID Connect in hetida designer. 

Hetida designer supports authentication via the OpenID Connect standard using the Auth Code flow with PKCE. Authentication has to be enabled in both the backend and the frontend. In addition, you will need an OpenID provider, for example [keycloak](https://www.keycloak.org/). 
## Setup

We save a copy of the `docker-compose-dev.yml` with the new name `docker-compose-keycloak.yml`, modify the **hetida-designer-backend** and the **hetida-designer-frontend** service and add a **keycloak** service as follows:

```yaml
...

  hetida-designer-backend:
    ...
    environment:
      ...
      - AUTH_ENABLED=true
      ...
    ...
...

  hetida-designer-frontend:
    ...
    volumes:
      - ./hetida_designer_config_keycloak.json:/usr/share/nginx/html/assets/hetida_designer_config.json
...

  hetida-designer-keycloak:
    image: jboss/keycloak
    ports:
      - 8081:8080
    environment:
      - KEYCLOAK_USER=admin
      - KEYCLOAK_PASSWORD=admin
      - KEYCLOAK_IMPORT=/tmp/hetida-designer-realm.json
    volumes:
      - ./hetida-designer-realm.json:/tmp/hetida-designer-realm.json    

...

```

In order to enable OpenID Connect in the frontend, we create a `hetida_designer_config_keycloak.json` file as follows and mount it into the `hetida-designer-web` service (see docker-compose file above):

```json

{
  ...,
  "authEnabled": true,
  "authConfig": {
    "authority": "http://localhost:8081/auth/realms/hetida-designer",
    "clientId": "hetida-designer",
    "userNameAttribute": "preferred_username"
  }
}

```

`authority` and `clientId` have to be provided in order for the login to work.
`userNameAttribute` is the name of the attribute in the id token which contains the username (needed to display the username in the UI).
For more configuration options see https://github.com/damienbod/angular-auth-oidc-client.

Our setup uses a pre-configured keycloak realm named `hetida-designer` which is imported from `hetida-designer-realm.json` and has an example user with the following credentials:

username: `testuser`\
password: `testpassword`

:warning: **You should not use this example setup in a production environment. Make sure you use sensible security defaults and secure credentials when configuring your OpenID provider.**

Once the user is logged in, the hetida designer frontend will add the access token to all REST requests (as a bearer token in the HTTP Authorization header).