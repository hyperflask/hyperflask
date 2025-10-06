from .core import ComponentAdapter


class AlpineAdapter(ComponentAdapter):
    @classmethod
    def matches(cls, app, module_name, template):
        if not template or not ComponentAdapter.matches(app, module_name, template):
            return False
        tpl = app.jinja_env.loader.get_source(app.jinja_env, template)[0]
        return any(tag in tpl for tag in ["x-data", "x-init"])

    def register(self, app, url_prefix):
        app.assets.include("@hyperflask/alpine")
        return super().register(app, url_prefix)
