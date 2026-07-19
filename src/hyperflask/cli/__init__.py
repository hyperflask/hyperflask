import os
import json
import click
from flask import current_app
from flask.cli import FlaskGroup, shell_command, routes_command, ScriptInfo, NoAppException
from flask_assets_pipeline import cli as assets_cli
from ..factory import create_app
from ..security import generate_csp_policy
from ..utils.freezer import StaticMode
from .runner import serve_command, run_command, dev_command
from .worker import worker_command, scheduler_command
from .scaffold import gen


def _create_app():
    try:
        if os.environ.get("FLASK_APP") == "0":
            raise NoAppException("")
        info = ScriptInfo(os.environ.get("FLASK_APP"))
        return info.load_app()
    except NoAppException:
        return create_app(os.environ.get("FLASK_ROOT"))


cli = FlaskGroup(name='kantree', help='Kantree', add_default_commands=False, create_app=_create_app)
cli.add_command(shell_command)
cli.add_command(routes_command)
cli.add_command(serve_command)
cli.add_command(run_command)
cli.add_command(dev_command)
cli.add_command(worker_command)
cli.add_command(scheduler_command)
cli.add_command(gen)


@cli.command("build")
@click.pass_context
def build_command(ctx):
    ctx.invoke(assets_cli.build)
    if StaticMode(current_app.config['STATIC_MODE']) != StaticMode.DYNAMIC:
        current_app.freezer.freeze()


@cli.command("csp-header")
def csp_header_command():
    click.echo(generate_csp_policy())


@cli.command("encode-session-cookie")
@click.argument("data")
def encode_session_cookie_command(data):
    """Encode a session cookie value from JSON data"""
    serializer = current_app.session_interface.get_signing_serializer(current_app)
    value = serializer.dumps(json.loads(data))
    click.echo(value)


@cli.command("decode-session-cookie")
@click.argument("cookie", required=False)
@click.option("--cookie-file", "-f", type=click.Path(exists=True), help="Path to a file containing a list of cookies (from test-request command)")
def decode_session_cookie_command(cookie, cookie_file):
    """Decode a session cookie value to JSON data"""
    if not cookie and cookie_file:
        with open(cookie_file, "r") as f:
            for cookie_data in f.readlines():
                key, value = cookie_data.split(";", 1)[0].split("=", 1)
                if key.strip() == current_app.config["SESSION_COOKIE_NAME"]:
                    cookie = value.strip()
                    break
    elif not cookie:
        click.echo("Either COOKIE argument or --cookie-file option must be provided", err=True)
        return
    try:
        serializer = current_app.session_interface.get_signing_serializer(current_app)
        data = serializer.loads(cookie)
        click.echo(json.dumps(data, indent=2))
    except Exception as e:
        click.echo("Cannot decode cookie value", err=True)
        return


@cli.command("test-request")
@click.argument("path")
@click.option("--method", "-m", default="GET", help="HTTP method to use")
@click.option("--data", "-d", default=None, help="Data to send with the request")
@click.option("--header", "-h", multiple=True, help="Headers to include in the request")
@click.option("--follow-redirects/--no-follow-redirects", default=True, help="Whether to follow redirects")
@click.option("--session", "-s", help="JSON data that will be used to populate the session cookie")
@click.option("--cookie", "-c", multiple=True, help="Cookies to include in the request")
@click.option("--cookie-file", "-f", type=click.Path(), help="Path to read and write cookies from, helpful for preserving cookies between requests")
@click.pass_context
def test_request_command(ctx, path, method, data, header, follow_redirects, cookie, session, cookie_file):
    """Simulate a request to the application and display the response. The path can include query parameters.
    """
    current_app.config["DEBUG_TB_ENABLED"] = False
    client = current_app.test_client()
    headers = []
    cookies = {}
    for header_ in header:
        key, value = header_.split(":", 1)
        headers.append((key.strip(), value.strip()))
    if cookie_file and os.path.exists(cookie_file):
        with open(cookie_file, "r") as f:
            for cookie_data in f.readlines():
                key, value = cookie_data.split(";", 1)[0].split("=", 1)
                cookies[key.strip()] = value.strip()
                client.set_cookie(key=key.strip(), value=value.strip())
    if cookie:
        for cookie_ in cookie:
            key, value = cookie_.split("=", 1)
            cookies[key.strip()] = value.strip()
            client.set_cookie(key=key.strip(), value=value.strip())
    if session:
        serializer = current_app.session_interface.get_signing_serializer(current_app)
        session_cookie = serializer.dumps(json.loads(session))
        client.set_cookie(key=current_app.config["SESSION_COOKIE_NAME"], value=session_cookie)

    resp = client.open(path=path, method=method, data=data, headers=headers, follow_redirects=follow_redirects)

    click.echo(f"HTTP/1.1 {resp.status}")
    for key, value in resp.headers.items():
        click.echo(f"{key}: {value}")
        if key.lower() == "set-cookie":
            name, value = value.split(";", 1)[0].split("=", 1)
            cookies[name.strip()] = value.strip()
    click.echo("")
    click.echo(resp.get_data(as_text=True))
    if cookie_file and cookies:
        with open(cookie_file, "w") as f:
            for name, value in cookies.items():
                f.write(f"{name}={value}\n")


def main():
    cli.main()
