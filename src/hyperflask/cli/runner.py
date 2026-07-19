from flask.cli import _debug_option, pass_script_info, run_command as flask_run_command
import click
import os
import sys
import multiprocessing
import gunicorn.app.base
from subprocess import Popen
from honcho.manager import Manager as BaseProcessManager
from honcho.command import _parse_concurrency
from honcho.environ import parse_procfile
from honcho.printer import Printer
from honcho import environ
from flask_configurator.config import Config
from ..factory import load_config
from . import reloader # import hacky patch of werkzeug reloader


@click.command("serve")
@click.option("--gunicorn/--no-gunicorn", default=True, is_flag=True, help="Use Gunicorn to serve the app.")
@click.option('--gunicorn-config')
@click.option("--init-db", is_flag=True)
@pass_script_info
@click.pass_context
def serve_command(ctx, info, host, port, gunicorn, gunicorn_config, init_db, **run_kwargs):
    if init_db:
        print("Initializing database...")
        Popen([sys.argv[0], "db", "init"]).wait()

    if not gunicorn or os.environ.get("FLASK_DEBUG") == "1":
        ctx.invoke(flask_run_command, host=host, port=port, **run_kwargs)
        return

    GunicornServer(info.load_app, {
        'proc_name': 'hyperflask',
        'bind': f'{host}:{port}',
        'workers': 1 + multiprocessing.cpu_count() * 2,
        'max_requests': 1000,
        'max_requests_jitter': 100
    }, gunicorn_config).run()


serve_command.params = flask_run_command.params + serve_command.params


@click.command("run")
@click.argument('processes', nargs=-1)
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option('--concurrency', help="Number of concurrent processes to run.")
@click.option("--extend-procfile", is_flag=True, help="Extend an existing Procfile instead of using it")
@click.option("--init-db/--no-init-db", is_flag=True, default=None, help="Initialize the database before starting processes.")
@click.option('--gunicorn-config', help="A gunicorn configuration value for the web process in production (in the form key=value)")
@click.option("--logfile", help="File to log output of all processes to instead of stdout.")
@click.option("--dev", is_flag=True, help="Run in development mode with debug enabled.")
def run_command(processes, host, port, concurrency, extend_procfile, init_db, gunicorn_config, logfile, dev):
    if dev:
        os.environ["FLASK_DEBUG"] = "1"

    if init_db is None and dev or init_db:
        print("Initializing database...")
        Popen([sys.argv[0], "db", "init"]).wait()

    config = load_config()

    if not dev and not config.get('SECRET_KEY'):
        print("Critical: No SECRET_KEY set, cannot run in production mode.")
        sys.exit(1)

    _processes = get_default_processes(dev=dev, gunicorn_config=gunicorn_config, host=host)

    for filename in [f"Procfile.{config['ENV']}", "Procfile"]:
        if os.path.exists(filename):
            with open(filename) as f:
                procfile = parse_procfile(f.read()).processes
            if extend_procfile:
                _processes.update(procfile)
            else:
                _processes = procfile
            break

    processes = {name: cmd for name, cmd in _processes.items() if not processes or name in processes}
    env = {}
    if dev:
        env = {"FLASK_DEBUG": "1"}
    else:
        env = {
            "MERCURE_SUBSCRIBER_SECRET_KEY": config.get("MERCURE_SUBSCRIBER_SECRET_KEY", config['SECRET_KEY']),
            "MERCURE_PUBLISHER_SECRET_KEY": config.get("MERCURE_PUBLISHER_SECRET_KEY", config['SECRET_KEY']),
        }

    print("Starting Hyperflask processes...")
    manager = create_process_manager(processes, port=port, concurrency=concurrency, env=env, logfile=logfile)
    manager.loop()
    sys.exit(manager.returncode)


run_command.params.insert(0, _debug_option)


@click.command("dev")
@click.pass_context
def dev_command(ctx, **kwargs):
    ctx.forward(run_command, dev=True)


dev_command.params = list(run_command.params)


def get_default_processes(dev=False, gunicorn_config=None, host="127.0.0.1"):
    processes = {
        "web": [sys.argv[0], "serve", "--host", host, "--port", "$PORT"],
        "worker": [sys.argv[0], "worker"],
        "scheduler": [sys.argv[0], "scheduler"]
    }
    if gunicorn_config:
        processes["web"].extend(["--gunicorn-config", gunicorn_config])
    if dev:
        processes["assets"] = [sys.argv[0], "assets", "dev"]
        processes["worker"].extend(["-p", "1", "-t", "1"])
    else:
        processes["mercurehub"] = [sys.executable, "-m", "flask_mercure_sse.server", "--port", "$PORT"]
    return processes


def create_process_manager(processes, port=5000, concurrency=None, env=None, logfile=None):
    processes = {name: " ".join(cmd) if isinstance(cmd, list) else cmd for name, cmd in processes.items()}
    manager = ProcessManager(Printer(sys.stdout, colour=True))
    if not env:
        env = {}
    env["BASE_PORT"] = str(port)
    for p in environ.expand_processes(processes,
                                      concurrency=_parse_concurrency(concurrency),
                                      port=port):
        e = os.environ.copy()
        e.update(env)
        e.update(p.env)
        manager.add_process(p.name, p.cmd, quiet=p.quiet, env=e)

    if logfile:
        log_file = open(logfile, "a")
        manager.printer.output = log_file

    return manager


class ProcessManager(BaseProcessManager):
    # This override prevents the manager to stop if the worker and scheduler exit because dramatiq is unused
    def _any_stopped(self):
        def has_exited_because_dramatiq_unavailable(name, p):
            return name.split('.')[0] in ('scheduler', 'worker') and p.get('returncode') == 10
        return any(not has_exited_because_dramatiq_unavailable(name, p) and p.get('returncode') is not None
                   for name, p in self._processes.items())


class GunicornServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app_loader, config_defaults=None, config_filename=None):
        self.app_loader = app_loader
        self.config_defaults = config_defaults or {}
        self.config_filename = config_filename
        super().__init__()

    def load_config(self):
        config = Config("", self.config_defaults, env_prefix="GUNICORN")
        config.load(self.config_filename, default_env="production")

        config = {key.lower(): value for key, value in config.items()
                  if key.lower() in self.cfg.settings and value is not None}

        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.app_loader()
