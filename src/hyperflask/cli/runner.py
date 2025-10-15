from flask.cli import _debug_option, pass_script_info, run_command as flask_run_command
import click
import os
import sys
import multiprocessing
import gunicorn.app.base
from subprocess import Popen
from honcho.manager import Manager as BaseProcessManager
from ..factory import load_config
from . import reloader # import hacky patch of werkzeug reloader


@click.command("serve")
@click.option('--gunicorn-opt', multiple=True)
@click.option("--init-db", is_flag=True)
@pass_script_info
@click.pass_context
def serve_command(ctx, info, host, port, gunicorn_opt, init_db, **run_kwargs):
    if init_db:
        print("Initializing database...")
        Popen([sys.argv[0], "db", "init"]).wait()

    if os.environ.get("FLASK_DEBUG") == "1":
        ctx.invoke(flask_run_command, host=host, port=port, **run_kwargs)
    else:
        options = {
            'proc_name': 'hyperflask',
            'bind': f'{host}:{port}',
            'workers': 1 + multiprocessing.cpu_count() * 2,
            'max_requests': 1000,
            'max_requests_jitter': 100
        }
        for opt in gunicorn_opt:
            key, value = opt.split('=', 1)
            options[key] = int(value) if value.isdigit() else value
        GunicornServer(info.load_app, options).run()


serve_command.params = flask_run_command.params + serve_command.params


@click.command("run")
@click.argument('processes', nargs=-1)
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option('--concurrency')
@click.option("--extend-procfile", is_flag=True)
@click.option("--init-db/--no-init-db", is_flag=True, default=None)
@click.option("--dev", is_flag=True)
def run_command(processes, host, port, concurrency, extend_procfile, init_db, dev):
    from honcho.command import _parse_concurrency
    from honcho.environ import parse_procfile
    from honcho.printer import Printer
    from honcho import environ

    if dev:
        os.environ["FLASK_DEBUG"] = "1"

    if init_db is None and dev or init_db:
        print("Initializing database...")
        Popen([sys.argv[0], "db", "init"]).wait()

    _processes = {}
    procfile = None
    config = load_config()

    if not dev and not config.get('SECRET_KEY'):
        print("Critical: No SECRET_KEY set, cannot run in production mode.")
        sys.exit(1)

    for filename in [f"Procfile.{config['ENV']}", "Procfile"]:
        if os.path.exists(filename):
            with open(filename) as f:
                procfile = parse_procfile(f.read()).processes
            break

    _processes = {
        "web": [sys.argv[0], "serve", "--host", host, "--port", "$PORT"],
        "worker": [sys.argv[0], "worker"],
        "scheduler": [sys.argv[0], "scheduler"]
    }
    if dev:
        _processes["assets"] = [sys.argv[0], "assets", "dev"]
        _processes["worker"].extend(["-p", "1", "-t", "1"])
    else:
        _processes["mercurehub"] = [sys.executable, "-m", "flask_mercure_sse.server", "--port", "$PORT"]

    if procfile and extend_procfile:
        _processes.update(procfile)
    elif procfile:
        _processes = procfile

    processes = {name: " ".join(_processes[name]) if isinstance(_processes[name], list) else _processes[name]
                 for name in _processes if not processes or name in processes}
    env = {}
    if not dev:
        env = {
            "MERCURE_SUBSCRIBER_SECRET_KEY": config.get("MERCURE_SUBSCRIBER_SECRET_KEY", config['SECRET_KEY']),
            "MERCURE_PUBLISHER_SECRET_KEY": config.get("MERCURE_PUBLISHER_SECRET_KEY", config['SECRET_KEY']),
        }

    manager = ProcessManager(Printer(sys.stdout, colour=True))
    for p in environ.expand_processes(processes,
                                      concurrency=_parse_concurrency(concurrency),
                                      port=port):
        e = os.environ.copy()
        e.update(env)
        e.update(p.env)
        manager.add_process(p.name, p.cmd, quiet=p.quiet, env=e)

    print("Starting Hyperflask processes...")
    manager.loop()
    sys.exit(manager.returncode)


run_command.params.insert(0, _debug_option)


@click.command("dev")
@click.pass_context
def dev_command(ctx, **kwargs):
    ctx.forward(run_command, dev=True)


dev_command.params = list(run_command.params)


class ProcessManager(BaseProcessManager):
    # This override prevents the manager to stop if the worker and scheduler exit because dramatiq is unused
    def _any_stopped(self):
        def has_exited_because_dramatiq_unavailable(name, p):
            return name.split('.')[0] in ('scheduler', 'worker') and p.get('returncode') == 10
        return any(not has_exited_because_dramatiq_unavailable(name, p) and p.get('returncode') is not None
                   for name, p in self._processes.items())


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
