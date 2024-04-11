from .app import Hyperflask, db
from .resources import Resource
from .api import Api
from flask_configurator import Config
import importlib
from importlib.abc import MetaPathFinder, SourceLoader
from importlib.util import spec_from_file_location
from importlib.machinery import SourceFileLoader
from importlib.metadata import entry_points
import logging
import os
import sys
import runpy


app = None
api = None


def load_config(root_path=None):
    debug = os.environ.get("FLASK_DEBUG") == "1"
    default_env = "development" if debug else "production"
    config = Config(root_path, defaults={
        "SQLORM_URI": "sqlite://app.db"
    })
    config.load("config.yml", default_env)
    if config["ENV"] == "development" and not config.get("SECRET_KEY"):
        logging.getLogger().warn("Missing SECRET_KEY has been automatically set to 'changeme' while in development mode")
        config["SECRET_KEY"] = "changeme"
    return config


def create_app(root_path=None):
    global app
    global api
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
        sys.meta_path.insert(0, VirtualPackageFinder(import_name, root_path))
    else:
        import_name = "__main__"

    app = Hyperflask(import_name, root_path=root_path, config=config, static_folder=static_folder,
                     static_url_path=config.get("STATIC_URL_PATH", "/static"),
                     migrations_folder=migrations_folder)
    
    api = Api(app)

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
    try_import(app, "api")
    try_import(app, "tasks")
    try_import(app, "cron")

    resources = try_import(app, "resources")
    if resources:
        for name in dir(resources):
            obj = getattr(resources, name)
            if issubclass(obj, Resource) and obj.url_prefix:
                obj.register(app, api)

    db.init_db()
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
    

def get_factory_package(name):
    tasks_dir = os.path.join(app.root_path, name)
    if not os.path.exists(os.path.join(app.root_path, f"{name}.py")) and os.path.isdir(tasks_dir) and not os.path.exists(os.path.join(tasks_dir, "__init__.py")):
        return tasks_dir
    return False


def create_task_from_file(app, filename, **kwargs):
    kwargs["actor_name"] = os.path.basename(filename).rsplit(".", 1)[0]
    @app.actor(**kwargs)
    def actor():
        runpy.run_path(filename)


def extract_cron_schedule_from_file(filename):
    with open(filename) as f:
        line = f.readline()
        if not line.startswith("#"):
            raise Exception("Cronjobs must start with a comment line specifying the schedule")
        return line[1:].strip()


class VirtualPackageFinder(MetaPathFinder):
    def __init__(self, package_name, path=None):
        if not path:
            path = os.path.join(os.getcwd(), package_name.replace(".", "/"))
        self.package_name = package_name
        self.path = path

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith(self.package_name):
            return
        
        if fullname == self.package_name:
            relname = ""
        else:
            relname = fullname[len(self.package_name)+1:].replace(".", "/")

        if os.path.isdir(os.path.join(self.path, relname)):
            filename = os.path.join(self.path, relname, "__init__.py")
            loader_class = SourceFileLoader if os.path.exists(filename) else EmptyFileLoader
            return spec_from_file_location(fullname, filename, loader=loader_class(fullname, filename),
                submodule_search_locations=[os.path.join(self.path, relname)])
        
        filename = os.path.join(self.path, f"{relname}.py")
        if os.path.exists(filename):
            return spec_from_file_location(fullname, filename, loader=SourceFileLoader(fullname, filename),
                                            submodule_search_locations=None)
        


class EmptyFileLoader(SourceLoader):
    def __init__(self, fullname, filename):
        self.fullname = fullname
        self.filename = filename

    def get_filename(self, fullname):
        return self.filename

    def get_data(self, filename):
        return ""
    

if __name__ == "__main__":
    create_app()