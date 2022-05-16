# eduTEAMS CLI

The eduTEAMS Command Line Interface allows the user to login using the Device Code Flow and retrieve an access_token, an id_token and a refresh_token.

## Install eduteams-cli in venv

```sh
poetry shell
poetry install
```

## Run eduTEAMS CLI

Set the scopes that you want to request:

```sh
export EDUTEAMS_SCOPE="openid profile"
```

Set the client id of your application:

```sh
export EDUTEAMS_CLIENT_ID="APP-12345-56789"
```

Set the issuer for the discovery code flow:

```sh
export EDUTEAMS_ISS="https://webapp.eduteams.org/oidc"
```

Run the application:

```sh
eduteams-cli login
```
