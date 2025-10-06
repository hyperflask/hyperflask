import click
import sys
from flask import current_app
from flask.cli import with_appcontext
import periodiq
from dramatiq import set_broker
from dramatiq.cli import (
    CPUS,
    main as dramatiq_worker,
    make_argument_parser as dramatiq_argument_parser,
)


@click.command("worker")
@click.option('-v', '--verbose', is_flag=True)
@click.option('-p', '--processes', default=CPUS,
              metavar='PROCESSES', show_default=True,
              help="the number of worker processes to run")
@click.option('-t', '--threads', default=8,
              metavar='THREADS', show_default=True,
              help="the number of worker threads per process")
@click.option('-Q', '--queues', type=str, default=None,
              metavar='QUEUES', show_default=True,
              help="listen to a subset of queues, comma separated")
@with_appcontext
def worker_command(verbose, processes, threads, queues):
    """Run dramatiq workers.
    """
    check_dramatiq_availability()

    parser = dramatiq_argument_parser()

    command = [
        "--processes", str(processes),
        "--threads", str(threads),
        # This module does not have broker local. Thus dramatiq fallbacks to
        # global broker.
        __name__,
    ]
    if verbose:
        command += ["-v"]
    if current_app.config['DEBUG']:
        command += ["--watch", current_app.root_path]

    queues = queues.split(",") if queues else []
    if queues:
        command += ["--queues"] + queues

    args = parser.parse_args(command)
    dramatiq_worker(args)


@click.command("scheduler")
@click.option('-v', '--verbose', is_flag=True)
@with_appcontext
def scheduler_command(verbose):
    """Run periodiq scheduler.
    """
    check_dramatiq_availability()

    periodic_actors = [
        a for a in current_app.dramatiq_broker.actors.values()
        if 'periodic' in a.options
    ]
    if not periodic_actors:
        click.echo("No scheduled Dramatiq actors found.")
        sys.exit(10)

    command = [
        # This module does not have broker local. Thus dramatiq fallbacks to
        # global broker.
        __name__,
    ]

    if verbose:
        command += ["-v"]

    parser = periodiq.make_argument_parser()
    args = parser.parse_args(command)
    periodiq.main(args)


def check_dramatiq_availability():
    if not getattr(current_app, 'dramatiq_broker', None):
        click.echo("Dramatiq broker is not configured.")
        sys.exit(10)
    if not current_app.dramatiq_broker.actors:
        click.echo("No Dramatiq actors found.")
        sys.exit(10)
    set_broker(current_app.dramatiq_broker)
