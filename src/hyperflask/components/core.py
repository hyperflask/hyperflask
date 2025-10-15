from markupsafe import Markup
from flask import request, current_app
from flask.views import http_method_funcs
from flask_file_routes import page
from flask_suspense import render_template
from jinjapy import extract_frontmatter
from ..utils.freezer import dynamic
import importlib
import re


class BaseComponentAdapter:
    @classmethod
    def matches(cls, app, module_name, template):
        return False

    def __init__(self, name, module_name, template, filename):
        self.name = name
        self.module_name = module_name
        self.template = template
        self.filename = filename

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
        methods = self.find_supported_http_methods(app)
        if methods:
            app.add_url_rule(url, self.name, view_func=self.view_func, methods=methods)

    @dynamic
    def view_func(self):
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
        if self.template:
            ctx = self.get_render_context(None, **props)
            return render_template(self.template, **ctx)
        if "render" in dir(module):
            return module.render(**props)
        return ""

    def find_supported_http_methods(self, app):
        # avoid importing the module early
        # need to read from filename otherwise frontmatter will be stripped
        filename = app.jinja_env.loader.get_source(app.jinja_env, self.filename)[1]
        with open(filename) as f:
            source, frontmatter = extract_frontmatter(f.read())
            if not self.template:
                frontmatter = source
            if not frontmatter:
                return []
            return [m.upper() for m in http_method_funcs if re.search(rf"^(def\s+{m}\()|{m}\s*=", frontmatter, re.MULTILINE)]

    def render(self, *args, **kwargs):
        caller = kwargs.pop('caller', None)
        if not self.template:
            if caller:
                kwargs['caller'] = caller
            return Markup(self.call_render_func(*args, **kwargs) or "")
        tpl = current_app.jinja_env.get_template(self.template)
        ctx = self.get_render_context(caller, *args, **kwargs)
        return Markup(tpl.render(ctx)) # do not use render_template() so we don't trigger flask signals

    def get_render_context(self, caller, *args, **kwargs):
        ctx = kwargs.pop('_ctx', {})
        ctx.update(dict(args=args, kwargs=kwargs, props=PropsWrapper(kwargs), caller=caller, children=caller))
        _ctx = self.call_render_func(*args, **kwargs)
        if _ctx:
            ctx.update(_ctx)
        return ctx

    def call_render_func(self, *args, **kwargs):
        if self.module_name:
            module = importlib.import_module(self.module_name)
            if module and "render" in dir(module):
                return module.render(*args, **kwargs)


class PropsWrapper:
    def __init__(self, props):
        self._props = props

    def __getattr__(self, name):
        if name in self._props:
            return self._props[name]
        raise Exception(f"No such prop: {name}")
