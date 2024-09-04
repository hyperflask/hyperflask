# flask
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader
from werkzeug.middleware.proxy_fix import ProxyFix
# hyperflask extensions
from jinja_layout import LayoutExtension
from jinja_wtforms import WtformExtension
from flask_assets_pipeline import AssetsPipeline
from flask_super_macros import SuperMacros
from flask_collections import Collections
from flask_file_routes import FileRoutes
from flask_configurator import Config
from flask_babel import Babel, _, _p, _n, _np, lazy_gettext
from flask_geo import Geolocation
from flask_files import Files
from flask_sqlorm import FlaskSQLORM
from flask_mercure_sse import MercureSSE
from flask_mailman_templates import MailTemplates
#from flask_observability import Observability
# 3rd party extensions
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_frozen import Freezer
from htmx_flask import Htmx
from flask_mailman import Mail
from flask_dramatiq import Dramatiq
from flask_debugtoolbar import DebugToolbarExtension
# from hyperflask
from .forms import Form
from .utils.page_actions import page_action_url
from .utils.htmx import htmx_oob
from .components import register_components
from . import page_helpers
# others
from jinja_super_macros.registry import FileLoader
from jinja_wtforms.extractor import map_jinja_call_node_to_func
from sqlorm.sql_template import SQLTemplate
from periodiq import PeriodiqMiddleware
import os


db = FlaskSQLORM()


map_jinja_call_node_to_func(_)
map_jinja_call_node_to_func(_p)
map_jinja_call_node_to_func(_n)
map_jinja_call_node_to_func(_np)
map_jinja_call_node_to_func(lazy_gettext)


class Hyperflask(Flask):
    config_class = Config

    def __init__(self, *args, static_mode="hybrid", instrument=False, layouts_folder="layouts", partials_folder="partials",
                 emails_folder="emails", forms_folder="forms", assets_folder="assets", pages_folder="pages", migrations_folder="migrations",
                 config=None, config_filename="config.yml", **kwargs):

        super().__init__(*args, **kwargs)
        self.wsgi_app = ProxyFix(self.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

        self.config.update({
            "FREEZER_DESTINATION": os.path.join(self.root_path, "_site"),
            "FREEZER_STATIC_IGNORE": [],
            "WTF_CSRF_CHECK_DEFAULT": False,
            "OTEL_INSTRUMENT": instrument,
            "DRAMATIQ_BROKER": "dramatiq.brokers.redis:RedisBroker",
            "DEBUG_TB_INTERCEPT_REDIRECTS": False,
            "PAGES_MARKDOWN_OPTIONS": {"extensions": ["fenced_code", "nl2br", "attr_list", "admonition", "codehilite"]},
            # Hyperflask specific
            "LAYOUT": "layout.html",
            "STATIC_MODE": static_mode,
            "ASSETS_INCLUDE_HTMX": True,
            "HTMX_BOOST_SITE": False
        })
        if config:
            self.config.update(config)
        if config_filename:
            self.config.load(config_filename)
        if self.debug:
            self.config.setdefault("MAIL_BACKEND", "console")

        #self.otel = Observability(self)

        self.jinja_env.add_extension(LayoutExtension)
        self.jinja_env.add_extension(WtformExtension)
        self.jinja_env.form_base_cls = Form
        self.jinja_env.default_layout = self.config["LAYOUT"]
        self.forms = self.jinja_env.forms

        self.jinja_env.loader = ChoiceLoader([self.jinja_env.loader])
        if layouts_folder and os.path.exists(os.path.join(self.root_path, layouts_folder)):
            layout_loader = FileSystemLoader(os.path.join(self.root_path, layouts_folder))
            self.jinja_env.loader.loaders.append(layout_loader)
            self.jinja_env.loader.loaders.append(PrefixLoader({os.path.basename(layouts_folder): layout_loader}))
        self.jinja_env.loader.loaders.extend([
            FileLoader(os.path.join(os.path.dirname(__file__), "layouts/web.html"), "layout.html"),
            FileLoader(os.path.join(os.path.dirname(__file__), "layouts/web.html"), "hyperflask_layout.html"),
            PrefixLoader({"ui": FileSystemLoader(os.path.join(os.path.dirname(__file__), "ui"))})
        ])

        DebugToolbarExtension(self)
        self.freezer = Freezer(self)
        self.csrf = CSRFProtect(self)
        #self.talisman = Talisman(self)
        Htmx(self)
        Mail(self)
        self.dramatiq = Dramatiq(self)
        self.dramatiq.broker.add_middleware(PeriodiqMiddleware())
        self.actor = self.dramatiq.actor

        SuperMacros(self)
        Babel(self)
        Geolocation(self)
        Files(self)
        MailTemplates(self, template_folder=emails_folder)
        file_routes = FileRoutes(self, pages_folder=pages_folder, partials_folder=partials_folder)
        self.page_helper = file_routes.page_helper
        self.collections = Collections(self)
        MercureSSE(self)

        self.assets = AssetsPipeline(self, assets_folder=assets_folder, inline=True, include_inline_on_demand=False)
        self.assets.state.watch_template_folders.extend([
            os.path.join(self.root_path, "pages"),
            os.path.join(self.root_path, "macros"),
            os.path.join(self.root_path, "components"),
            os.path.join(self.root_path, "forms")
        ])
        self.assets.state.esbuild_aliases.update({
            "assets": self.assets.state.assets_folder,
            "@hyperflask": os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
        })
        self.assets.state.tailwind_suggested_content.extend(filter(bool, [
            os.path.join(os.path.dirname(__file__), "ui") + "/**/*.html",
            os.path.join(self.root_path, pages_folder) + "/**/*.html" if pages_folder else None,
            os.path.join(self.root_path, pages_folder) + "/**/*.jpy" if pages_folder else None,
            os.path.join(self.root_path, partials_folder) + "/**/*.html" if partials_folder else None,
            os.path.join(self.root_path, partials_folder) + "/**/*.jpy" if partials_folder else None,
            os.path.join(self.root_path, layouts_folder) + "/**/*.html" if layouts_folder else None,
            os.path.join(self.root_path, "components") + "/**/*.html",
            os.path.join(self.root_path, "components") + "/**/*.jpy",
        ]))
        self.assets.state.copy_files_from_node_modules.update({
            "bootstrap-icons/font": "bootstrap-icons"
        })
        self.assets.bundle(
            {"@hyperflask": ["app.js"],
             "@hyperflask/reactive": ["reactive.js"],
             "@hyperflask/alpine": ["alpine.js"]},
            assets_folder=os.path.join(os.path.dirname(__file__), "static")
        )
        self.assets.include("@hyperflask", 0)

        self.extensions['mail_templates'].jinja_env.add_extension(LayoutExtension)
        self.extensions['mail_templates'].jinja_env.default_layout = "layout.mjml"
        self.extensions['mail_templates'].loaders.extend([
            FileLoader(os.path.join(os.path.dirname(__file__), 'layouts/email.mjml'), 'layout.mjml'),
            FileLoader(os.path.join(os.path.dirname(__file__), 'layouts/email.mjml'), 'hyperflask_layout.mjml')
        ])

        self.macros.register_from_directory(os.path.join(os.path.dirname(__file__), "ui"))
        if hasattr(file_routes, "loader"):
            self.forms.register_from_loader(file_routes.loader, "pages")
        self.macros.create_from_func(htmx_oob, "HtmxOob", receive_caller=True, caller_alias="html")
        register_components(self)

        if forms_folder and os.path.isdir(os.path.join(self.root_path, forms_folder)):
            for macro in self.macros.create_from_directory(os.path.join(self.root_path, forms_folder)):
                self.forms.register(self.macros.resolve_template(macro), macro)

        self.jinja_env.globals.update(page_action_url=page_action_url)

        self.collections.register_freezer_generator(self.freezer)

        SQLTemplate.eval_globals.update(app=self)
        db.init_app(self, migrations_folder=migrations_folder)


def static(func):
    pass


def dynamic(func=None, static_template=None):
    def decorator(func):
        pass
    return decorator(func) if func else decorator
