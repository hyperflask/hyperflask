from flask import current_app
from flask.cli import FlaskGroup, shell_command, routes_command, ScriptInfo, NoAppException
from flask_assets_pipeline import cli as assets_cli
import click
from ..factory import create_app
from ..security import generate_csp_policy
from ..utils.freezer import StaticMode
from .runner import serve_command, run_command, dev_command
from .worker import worker_command, scheduler_command


def _create_app():
    info = ScriptInfo()
    try:
        return info.load_app()
    except NoAppException:
        return create_app()


cli = FlaskGroup(name='kantree', help='Kantree', add_default_commands=False, create_app=_create_app)
cli.add_command(shell_command)
cli.add_command(routes_command)
cli.add_command(serve_command)
cli.add_command(run_command)
cli.add_command(dev_command)
cli.add_command(worker_command)
cli.add_command(scheduler_command)


@cli.command("init")
def init_command():
    pass


@cli.command("build")
@click.pass_context
def build_command(ctx):
    ctx.invoke(assets_cli.build)
    if StaticMode(current_app.config['STATIC_MODE']) != StaticMode.DYNAMIC:
        current_app.freezer.freeze()


@cli.command("csp-header")
def csp_header_command():
    click.echo(generate_csp_policy())


def main():
    cli.main()
