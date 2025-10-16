from flask.cli import AppGroup, with_appcontext
import random
import click
import os


gen = AppGroup('gen', help='Generate various files and code snippets.')


@gen.command('secret-key')
@click.option('--save/--no-save', is_flag=True, default=True, help='Save the generated key to the .env file.')
def generate_secret_key_command(save):
    key = generate_secret_key()
    if save:
       save_env_var("FLASK_SECRET_KEY", key)
    click.echo(key)


def generate_secret_key():
    return ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])


def save_env_var(key, value):
    env = []
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            env = f.readlines()
    with open(".env", "w") as f:
        for line in env:
            if not line.startswith(f"{key}="):
                f.write(f"{line}\n")
        f.write(f"{key}={value}\n")
