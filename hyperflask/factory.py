from .app import Hyperflask, db
from flask_configurator import Config
import importlib
from importlib.abc import MetaPathFinder, SourceLoader
from importlib.util import spec_from_file_location
from importlib.machinery import SourceFileLoader
from importlib.metadata import entry_points
import os
import sys


app = None


def load_config(root_path=None):
    default_env = "development" if os.environ.get("FLASK_DEBUG") == "1" else "production"
    config = Config(root_path, defaults={
        "SQLORM_URI": "sqlite://app.db"
    })
    config.load("config.yml", default_env)
    return config


def create_app(root_path=None):
    global app
    config = load_config(root_path)
    static_folder = config.get("STATIC_FOLDER", "public")
    migrations_folder = config.get("MIGRATIONS_FOLDER", "migrations")

    if not root_path:
        import_name = "__main__"
        root_path = os.getcwd()
    else:
        import_name = os.path.basename(root_path)
        sys.meta_path.insert(0, VirtualPackageFinder(import_name, root_path))
        static_folder = os.path.abspath(os.path.join(root_path, static_folder))
        migrations_folder = os.path.abspath(os.path.join(root_path, migrations_folder))

    app = Hyperflask(import_name, root_path=root_path, config=config, static_folder=static_folder,
                     static_url_path=config.get("STATIC_URL_PATH", "/static"),
                     migrations_folder=migrations_folder)
    
    try_import(app, "models")
    try_import(app, "routes")

    if not try_import(app, "tasks"):
        if register_virtual_package("tasks"):
            for f in os.listdir("tasks"):
                # register task
                pass

    if register_virtual_package("cron"):
        for f in os.listdir("cron"):
            # register task
            pass

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

    db.init_db()

    return app


def try_import(app, name):
    if app.import_name != "__main__":
        name = f"{app.import_name}.{name}"
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def register_virtual_package(name):
    if os.path.exists(name):
        sys.meta_path.insert(0, VirtualPackageFinder(name))
        return True
    return False


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