import jinjapy
import importlib
import os
import importlib
import re
from importlib.metadata import entry_points
from .core import ComponentAdapter
from .alpine import AlpineAdapter
from .webcomponent import WebComponentAdapter
from .jsx import ReactAdapter


def discover_components(app, path=None, package_name=None):
    if not path:
        path = os.path.join(app.root_path, "components")
        if not os.path.exists(path):
            return None, []
    if not package_name:
        package_name = app.relative_import_name("components")


    adapters = list(list_available_adapters())
    force_adapters = app.config.get("COMPONENT_ADAPTERS", {})
    components = []

    loader = jinjapy.register_package(package_name, path, env=app.jinja_env)
    for module_name, template in loader.list_files(module_with_package=False):
        filename = template or (loader.prefix + module_name.replace(".", os.sep) + ".py")
        adapter_class = None
        for pattern, adapter_import_path in force_adapters.items():
            if re.match(pattern, filename):
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
            name = (os.path.basename(template).split(".")[0] if template else module_name.split('.')[-1]).replace("-", "_")
            adapter = adapter_class(name, f"{package_name}.{module_name}" if module_name else None, template, filename)
            components.append(adapter)

    return loader, components


def register_components(app, path=None, package_name=None, url_prefix="/__components/"):
    loader, adapters = discover_components(app, path, package_name)
    for adapter in adapters:
        adapter.register(app, url_prefix)
    return loader, adapters


def list_available_adapters():
    yield AlpineAdapter
    yield WebComponentAdapter
    yield ReactAdapter
    for entry in entry_points(group="hyperflask.component_adapters"):
        yield entry.load()
    yield ComponentAdapter
