import typer
import requests
import qrcode
import datetime
import time
import io
import click
import json
import os

ISS = "https://webapp.eduteams.org/oidc"
CLIENT_ID = "APP-12345-56789"
SCOPE = "openid+profile"

app = typer.Typer()


@app.callback()
def callback():
    """
    eduTEAMS CLI
    """


@app.command()
def login(
    iss: str = typer.Argument(ISS, envvar="EDUTEAMS_ISS"),
    client_id: str = typer.Argument(CLIENT_ID, envvar="EDUTEAMS_CLIENT_ID"),
    scope: str = typer.Argument(SCOPE, envvar="EDUTEAMS_SCOPE"),
):
    openid_config = get_openid_config(iss)
    response = get_device_code(openid_config, client_id, scope)
    device_code = response.get("device_code")
    user_code = response.get("user_code")
    expire_at = int(datetime.datetime.utcnow().timestamp()) + int(
        response.get("expire_in")
    )
    interval = response.get("interval", 5)
    verification_uri = response.get("verification_uri")
    verification_uri_complete = response.get("verification_uri_complete")
    qr = get_qr_code(verification_uri_complete)
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    click.clear()
    typer.echo("Scan the QR code or, using a browser on another device, visit:\n")
    typer.echo(f"{verification_uri}\n")
    typer.echo(f"And enter the code: {user_code}")
    print(f.read())
    typer.secho("\tDo not close the terminal", fg=typer.colors.MAGENTA)
    tokens = get_tokens(openid_config, interval, client_id, device_code)


def get_openid_config(iss: str):
    try:
        r = requests.get(iss + "/.well-known/openid-configuration")
        return r.json()
    except Exception:
        typer.echo(f"Could not discover the OpenID configuration for {iss}")
        raise typer.Exit()


def get_device_code(config: dict, client_id: str, scope: str):
    endpoint = config.get("device_authorization_endpoint")
    try:
        r = requests.get(endpoint, params={"client_id": client_id, "scope": scope})
        return r.json()
    except Exception:
        typer.echo("Could not retrieve device code")
        raise typer.Exit()


def get_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr


def get_tokens(config, interval, client_id, device_code):
    time.sleep(interval)
    endpoint = config.get("token_endpoint")
    data = {
        "client_id": client_id,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    r = requests.post(endpoint, data)
    status_code = r.status_code
    body = r.json()
    if status_code == 400:
        error = body.get("error")
        if error == "authorization_pending":
            get_tokens(config, interval, client_id, device_code)
        elif error == "slow_down":
            get_tokens(config, interval + 5, client_id, device_code)
        elif error == "access_denied":
            typer.echo("The authorization request was denied.")
            raise typer.Exit()
        elif error == "expired_token":
            typer.echo("The device_code has expired")
            raise typer.Exit()
    elif status_code == 200:
        click.clear()
        typer.secho(json.dumps(body, indent=4, sort_keys=True), fg=typer.colors.YELLOW)
    else:
        typer.echo("Unknown error")
        typer.echo(status_code)
        typer.echo(body)
        raise typer.Exit()
