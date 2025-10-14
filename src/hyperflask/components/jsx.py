from .core import BaseComponentAdapter
from markupsafe import Markup
from flask import current_app
from flask_assets_pipeline import BundleEntrypoint
import json
import html


class JsxComponentAdapter(BaseComponentAdapter):
    def register(self, app, url_prefix):
        super().register(app, url_prefix)
        if "@components" not in app.assets.state.bundles:
            app.assets.state.bundles["@components"] = []
            app.assets.include("@components")
        app.assets.state.bundles["@components"].append(
            BundleEntrypoint.create(self.template, from_package="jinja"))
        app.assets.include(self.include_js)

    def render(self, caller, *args, **kwargs):
        props = html.escape(json.dumps(kwargs), quote=True)
        _, scripts, styles = current_app.assets.split_urls(f"jinja:{self.template}", with_meta=True)
        current_app.assets.include([(scripts[0][0], "modulepreload")] + [(url, "modulepreload") for url, meta in scripts[1:] if meta.get("modifier") == "modulepreload"])
        current_app.assets.include(styles)
        return Markup(f'<{self.html_element} component-url="{scripts[0][0]}" props="{props}"></{self.html_element}>')


class ReactAdapter(JsxComponentAdapter):
    include_js = "@hyperflask/react"
    html_element = "hf-react-component"

    def register(self, app, url_prefix):
        if "@hyperflask/react" not in app.assets.state.bundles:
            app.assets.bundle({"@hyperflask/react": ["react.js"]},
                               from_package="hyperflask",
                               assets_folder="static")

        super().register(app, url_prefix)

    @classmethod
    def matches(cls, app, module_name, template):
        return template and (template.endswith(".jsx") or template.endswith(".tsx"))
