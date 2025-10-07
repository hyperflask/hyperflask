from flask.cli import _debug_option, pass_script_info, run_command as flask_run_command
import click
import os
import sys
import multiprocessing
import gunicorn.app.base
from honcho.manager import Manager as BaseProcessManager
from ..factory import load_config
from . import reloader # import hacky patch of werkzeug reloader


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


@click.command("run")
@click.argument('processes', nargs=-1)
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=5000, help="The port to bind to.")
@click.option('--concurrency')
@click.option("--extend-procfile")
@click.option("--dev", is_flag=True)
def run_command(processes, host, port, concurrency, extend_procfile, dev):
    from honcho.command import _procfile, _parse_concurrency
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
    if _processes is None or extend_procfile:
        if not _processes:
            _processes = {}
        _processes.update({
            "web": [sys.argv[0], "serve", "--host", host, "--port", "$PORT"],
            "worker": [sys.argv[0], "worker"],
            "scheduler": [sys.argv[0], "scheduler"]
        })
        if dev:
            _processes["assets"] = [sys.argv[0], "assets", "dev"]
            _processes["worker"].extend(["-p", "1", "-t", "1"])
        else:
            _processes["mercurehub"] = [sys.executable, "-m", "flask_mercure_sse.server"]

    processes = {name: " ".join(_processes[name]) if isinstance(_processes[name], list) else _processes[name]
                 for name in _processes if name in _processes}

    manager = ProcessManager(Printer(sys.stdout, colour=True))

    for p in environ.expand_processes(processes,
                                      concurrency=_parse_concurrency(concurrency),
                                      port=port):
        e = os.environ.copy()
        e.update(p.env)
        if p.name != "scheduler":
            e["FLASK_SKIP_DB_INIT"] = "0"
        manager.add_process(p.name, p.cmd, quiet=p.quiet, env=e)

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
