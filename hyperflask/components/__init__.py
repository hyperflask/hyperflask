import jinjapy
import importlib
import os
import importlib
import re
from importlib.metadata import entry_points
from .core import ComponentAdapter
from .alpine import AlpineAdapter
from .webcomponent import WebComponentAdapter


def register_components(app, path=None, package_name=None):
    if not path:
        path = os.path.join(app.root_path, "components")
        if not os.path.exists(path):
            return
    if not package_name:
        package_name = "components"
        if app.import_name != "__main__":
            package_name = f"{app.import_name}.{package_name}"

    url_prefix = "/__components/"
    adapters = list(list_available_adapters())
    force_adapters = app.config.get("COMPONENT_ADAPTERS", {})

    loader = jinjapy.register_package(package_name, path, env=app.jinja_env)
    for module_name, template in loader.list_files(module_with_package=False):
        adapter_class = None
        for pattern, adapter_import_path in force_adapters.items():
            if re.match(pattern, template):
                adapter_module, adapter_classname = adapter_import_path.split(":")
                adapter_class = getattr(importlib.import_module(adapter_module), adapter_classname)
                break
        if not adapter_class:
            matches = False
            for adapter_class in adapters:
                if adapter_class.matches(app, module_name, template):
                    matches = True
                    break
            if not matches:
                continue
        if adapter_class:
            name = os.path.basename(template).split(".")[0].replace("-", "_")
            adapter = adapter_class(name, f"{package_name}.{module_name}" if module_name else None, template)
            adapter.register(app, url_prefix)
            app.macros.create_from_func(adapter.render, name, receive_caller=True)


def list_available_adapters():
    yield AlpineAdapter
    yield WebComponentAdapter
    for entry in entry_points(group="hyperflask.component_adapters"):
        yield entry.load()
    yield ComponentAdapter
