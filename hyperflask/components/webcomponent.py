from .core import BaseComponentAdapter
from jinja_super_macros import html_tag
from flask import current_app
from markupsafe import Markup
import os


class WebComponentAdapter(BaseComponentAdapter):
    @classmethod
    def matches(cls, app, module_name, template):
        return template.endswith(".js")

    def register(self, app, url_prefix):
        tpl = app.jinja_env.get_template(self.template)
        if "@components" not in app.assets.state.bundles:
            app.assets.state.bundles["@components"] = []
        app.assets.state.bundles["@components"].append(
            app.assets.format_bundle_file(os.path.abspath(tpl.filename), self.template))
    
    def render(self, caller, *args, **kwargs):
        current_app.assets.include("@components")
        tag_name = self.name.replace("_", "-")
        return html_tag(tag_name, **kwargs) + (caller() if caller else "") + Markup(f"</{tag_name}>")