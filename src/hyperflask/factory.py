from flask_configurator import Config
import importlib
from importlib.metadata import entry_points
import logging
import os
from .app import Hyperflask


app = None
db = None


def load_config(root_path=None):
    debug = os.environ.get("FLASK_DEBUG") == "1"
    default_env = "development" if debug else "production"
    config = Config(root_path)
    config.load("config.yml", default_env)
    if config["ENV"] == "development" and not config.get("SECRET_KEY"):
        logging.getLogger().warn("Missing SECRET_KEY has been automatically set to 'changeme' while in development mode")
        config["SECRET_KEY"] = "changeme"
    return config


def create_app(root_path=None):
    global app
    global db
    config = load_config(root_path)
    static_folder = config.get("STATIC_FOLDER", "public")
    migrations_folder = config.get("MIGRATIONS_FOLDER", "migrations")

    if root_path is None:
        root_path = os.getcwd()

    if os.path.exists(os.path.join(root_path, "app")):
        static_folder = os.path.abspath(os.path.join(root_path, static_folder))
        migrations_folder = os.path.abspath(os.path.join(root_path, migrations_folder))
        import_name = "app"
        root_path = os.path.join(root_path, "app")
    else:
        import_name = "__main__"

    app = Hyperflask(import_name, root_path=root_path, config_filename=None, config=config,
                     static_folder=static_folder, static_url_path=config.get("STATIC_URL_PATH", "/static"),
                     migrations_folder=migrations_folder)

    db = app.db

    if app.config.get("LOAD_HYPERFLASK_EXTENSIONS", True):
        for entry in entry_points(group="hyperflask.extensions"):
            entry.load()(app)

    extensions = {}
    if "FLASK_EXTENSIONS" in app.config:
        extensions.update(dict([ext.items()[0] if isinstance(ext, dict) else (ext, {}) for ext in app.config["FLASK_EXTENSIONS"]]))

    for ext, config in extensions.items():
        module, class_name = ext.rsplit(":", 1)
        m = importlib.import_module(module)
        getattr(m, class_name)(app, **config)

    try_import(app, "models")
    try_import(app, "routes")
    try_import(app, "actors")
    try_import(app, "tasks")
    try_import(app, "cron")
    try_import(app, "cli")
    try_import(app, "signals")
    try_import(app, "app")

    return app


def try_import(app, name, import_submodules=True):
    if app.import_name != "__main__":
        name = f"{app.import_name}.{name}"
    try:
        mod = importlib.import_module(name)

        if import_submodules:
            is_virtual_package = os.path.isdir(os.path.join(app.root_path, name)) and not os.path.exists(os.path.join(app.root_path, name, "__init__.py"))
            if is_virtual_package:
                mod = {}
                for f in os.listdir(os.path.join(app.root_path, name)):
                    if f.endswith(".py"):
                        m = importlib.import_module(f"{name}.{f.rsplit('.', 1)[0]}")
                        mod.update({k: getattr(m, k) for k in dir(m) if not k.startswith("_")})
                return mod

        return {k: getattr(mod, k) for k in dir(mod) if not k.startswith("_")}
    except ImportError:
        return


if __name__ == "__main__":
    create_app()
