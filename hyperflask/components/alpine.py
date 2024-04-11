from .core import ComponentAdapter
from flask import current_app


class AlpineAdapter(ComponentAdapter):
    @classmethod
    def matches(cls, app, module_name, template):
        if not ComponentAdapter.matches(app, module_name, template):
            return False
        tpl = app.jinja_env.loader.get_source(app.jinja_env, template)[0]
        tags = ["x-data", "x-init", "x-show", "x-bind", "x-model", "x-text", "x-html", "x-if", "x-for", "x-on"]
        return any(tag in tpl for tag in tags)

    def render(self, caller, *args, **kwargs):
        current_app.assets.include("@hyperflask/alpine")
        return super().render(caller, *args, **kwargs)
