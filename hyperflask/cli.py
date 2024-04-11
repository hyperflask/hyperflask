from flask import current_app
from flask.cli import FlaskGroup, shell_command, routes_command, _debug_option, pass_script_info, run_command as flask_run_command, ScriptInfo, NoAppException
from flask_assets_pipeline import cli as assets_cli
import click
import os
import sys
import multiprocessing
import gunicorn.app.base
from .factory import load_config, create_app


def _create_app():
    info = ScriptInfo()
    try:
        return info.load_app()
    except NoAppException:
        raise
        return create_app()


cli = FlaskGroup(name='kantree', help='Kantree', add_default_commands=False, create_app=_create_app)
cli.add_command(shell_command)
cli.add_command(routes_command)


@click.command("freeze")
def freeze_command():
    current_app.freezer.freeze()

cli.add_command(freeze_command)


@click.command("build")
@click.pass_context
def build_command(ctx):
    ctx.invoke(assets_cli.build)

cli.add_command(build_command)


@click.command("serve")
@click.option('--gunicorn-opt', multiple=True)
@pass_script_info
@click.pass_context
def serve_command(ctx, info, host, port, gunicorn_opt, **run_kwargs):
    if os.environ.get("FLASK_DEBUG") == "1":
        ctx.invoke(flask_run_command, host=host, port=port, **run_kwargs)
    else:
        options = {
            'proc_name': 'hyperflask',
            'bind': f'{host}:{port}',
            'workers': 1 + multiprocessing.cpu_count() * 2,
            'accesslog': '-',
            'errorlog': '-',
            'max_requests': 1000,
            'max_requests_jitter': 100
        }
        for opt in gunicorn_opt:
            key, value = opt.split('=', 1)
            options[key] = int(value) if value.isdigit() else value
        GunicornServer(info.load_app, options).run()


serve_command.params = flask_run_command.params + serve_command.params
cli.add_command(serve_command)


@click.command("run")
@click.argument('processes', nargs=-1)
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option('--concurrency')
@click.option("--dev", is_flag=True)
def run_command(processes, host, port, concurrency, dev):
    from honcho.command import _procfile, _parse_concurrency
    from honcho.manager import Manager
    from honcho.printer import Printer
    from honcho import environ

    if dev:
        os.environ["FLASK_DEBUG"] = "1"

    _processes = None
    config = load_config()
    for filename in [f"Procfile.{config['ENV']}", "Procfile"]:
        if os.path.exists(filename):
            _processes = _procfile(filename).processes
            break
    if _processes is None:
        _processes = {
            "web": [sys.argv[0], "serve", "--host", host, "--port", "$PORT"],
            # "worker": [sys.argv[0], "worker"],
            # "scheduler": [sys.argv[0], "periodiq"]
        }
        if dev:
            _processes["assets"] = [sys.argv[0], "assets", "dev"]

    processes = {name: " ".join(_processes[name]) if isinstance(_processes[name], list) else _processes[name]
                 for name in _processes if name in _processes}

    manager = Manager(Printer(sys.stdout, colour=True))

    for p in environ.expand_processes(processes,
                                      concurrency=_parse_concurrency(concurrency),
                                      port=port):
        e = os.environ.copy()
        e.update(p.env)
        manager.add_process(p.name, p.cmd, quiet=p.quiet, env=e)

    manager.loop()
    sys.exit(manager.returncode)


run_command.params.insert(0, _debug_option)
cli.add_command(run_command)


@click.command("dev")
@click.pass_context
def dev_command(ctx, **kwargs):
    ctx.forward(run_command, dev=True)


dev_command.params = list(run_command.params)
cli.add_command(dev_command)


def main():
    cli.main()


class GunicornServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app_loader, options=None):
        self.app_loader = app_loader
        self.options = options or {}
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.app_loader()
