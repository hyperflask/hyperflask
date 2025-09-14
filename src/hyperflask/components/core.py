from markupsafe import Markup
from flask import request, current_app
from flask.views import http_method_funcs
from flask_file_routes import page
from jinjapy import extract_frontmatter
import importlib
import re


class BaseComponentAdapter:
    @classmethod
    def matches(cls, app, module_name, template):
        return False

    def __init__(self, name, module_name, template):
        self.name = name
        self.module_name = module_name
        self.template = template

    def register(self, app, url_prefix):
        app.macros.create_from_func(self.render, self.name, receive_caller=True)

    def render(self, caller, *args, **kwargs):
        tpl = current_app.jinja_env.get_template(self.template)
        ctx = dict(args=args, kwargs=kwargs, props=kwargs, caller=caller)
        return Markup(tpl.render(**ctx))


class ComponentAdapter(BaseComponentAdapter):
    @classmethod
    def matches(cls, app, module_name, template):
        return module_name or template.endswith(".html") or template.endswith(".jpy")

    def register(self, app, url_prefix):
        super().register(app, url_prefix)
        if not self.module_name:
            return
        url = url_prefix + self.name.replace("_", "/")

        # avoid importing the module early
        # need to read from filename otherwise frontmatter will be stripped
        filename = app.jinja_env.loader.get_source(app.jinja_env, self.template)[1]
        with open(filename) as f:
            source = extract_frontmatter(f.read())[1]
            methods = [m.upper() for m in http_method_funcs if re.search(f"^(def\s+{m}\()|{m}\s*=", source, re.MULTILINE)]

        def view_func():
            props = {}
            page.template = self.template
            module = importlib.import_module(self.module_name)
            m = getattr(module, request.method.lower(), None)
            if m:
                props = m()
                if props is not None and not isinstance(props, dict):
                    return props
                if not props:
                    props = {}
            return self.render(None, **props)

        if methods:
            app.add_url_rule(url, self.name, view_func=view_func, methods=methods)

    def render(self, caller, *args, **kwargs):
        tpl = current_app.jinja_env.get_template(self.template)
        ctx = kwargs.pop('_ctx', {})
        ctx.update(dict(args=args, kwargs=kwargs, props=kwargs, caller=caller, children=caller))
        if self.module_name:
            module = importlib.import_module(self.module_name)
            if module and "render" in dir(module):
                _ctx = module.render(*args, **kwargs)
                if _ctx:
                    ctx.update(_ctx)
        return Markup(tpl.render(**ctx))
