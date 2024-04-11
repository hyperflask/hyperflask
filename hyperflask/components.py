from flask import request
from markupsafe import Markup
import jinjapy
import importlib
import os


def register_components(app):
    path = os.path.join(app.root_path, "components")
    if not os.path.exists(path):
        return
    url_prefix = "/__components/"
    package_name = "components"
    if app.import_name != "__main__":
        package_name = f"{app.import_name}.{package_name}"
    loader = jinjapy.register_package(package_name, path, env=app.jinja_env)
    for module_name, template in loader.list_files(module_with_package=False):
        create_component(app, package_name, module_name, template, url_prefix)


def create_component(app, package_name, module_name, template, url_prefix):
    macro_name = module_name.replace(".", "_")
    module = None

    if module_name:
        url = url_prefix + module_name.replace(".", "/")
        module = importlib.import_module(f"{package_name}.{module_name}")
        methods = filter(lambda m: m in dir(module), ["get", "post", "put", "patch", "delete"])
        def view_func():
            props = {}
            module = importlib.import_module(f"{package_name}.{module_name}")
            m = getattr(module, request.method.lower(), None)
            if m:
                props = m()
                if props and not isinstance(props, dict):
                    return props
                if not props:
                    props = {}
            return app.macros[macro_name](**props)
        if methods:
            app.add_url_rule(url, macro_name, view_func=view_func, methods=methods)

    def macro(caller, *args, **kwargs):
        ctx = dict(args=args, kwargs=kwargs, props=kwargs, caller=caller)
        tpl = app.jinja_env.get_template(template)
        module = importlib.import_module(f"{package_name}.{module_name}")
        if module and "render" in dir(module):
            _ctx = module.render(*args, **kwargs)
            if _ctx:
                ctx.update(_ctx)
        return Markup(tpl.render(**ctx))

    app.macros.create_from_func(macro, macro_name, receive_caller=True)