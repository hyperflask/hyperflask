from markupsafe import Markup
from flask import request, current_app
from flask.views import http_method_funcs
import importlib


class BaseComponentAdapter:
    @classmethod
    def matches(cls, app, module_name, template):
        return False

    def __init__(self, name, module_name, template):
        self.name = name
        self.module_name = module_name
        self.template = template

    def register(self, app, url_prefix):
        pass

    def render(self, caller, *args, **kwargs):
        tpl = current_app.jinja_env.get_template(self.template)
        ctx = dict(args=args, kwargs=kwargs, props=kwargs, caller=caller)
        return Markup(tpl.render(**ctx))


class ComponentAdapter(BaseComponentAdapter):
    @classmethod
    def matches(cls, app, module_name, template):
        return module_name or template.endswith(".html") or template.endswith(".jpy")

    def register(self, app, url_prefix):
        if not self.module_name:
            return
        url = url_prefix + self.name.replace("_", "/")
        module = importlib.import_module(self.module_name)
        methods = [m.upper() for m in http_method_funcs if m in dir(module)]
        def view_func():
            props = {}
            module = importlib.import_module(self.module_name)
            m = getattr(module, request.method.lower(), None)
            if m:
                props = m()
                if props is not None and not isinstance(props, dict):
                    return props
                if not props:
                    props = {}
            return app.macros[self.name](**props)
        if methods:
            app.add_url_rule(url, self.name, view_func=view_func, methods=methods)

    def render(self, caller, *args, **kwargs):
        tpl = current_app.jinja_env.get_template(self.template)
        ctx = dict(args=args, kwargs=kwargs, props=kwargs, caller=caller)
        if self.module_name:
            module = importlib.import_module(self.module_name)
            if module and "render" in dir(module):
                _ctx = module.render(*args, **kwargs)
                if _ctx:
                    ctx.update(_ctx)
        return Markup(tpl.render(**ctx))
