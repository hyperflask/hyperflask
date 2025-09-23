# flask
from flask import Flask
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader, TemplateNotFound
from werkzeug.middleware.proxy_fix import ProxyFix
# hyperflask extensions
from jinja_layout import LayoutExtension
from jinja_wtforms import WtformExtension
from flask_assets_pipeline import AssetsPipeline
from flask_super_macros import SuperMacros
from flask_collections import Collections
from flask_file_routes import FileRoutes, ModuleView, page
from flask_configurator import Config
from flask_babel import Babel, _, _p, _n, _np, lazy_gettext
from flask_geo import Geolocation
from flask_files import Files
from flask_sqlorm import FlaskSQLORM
from flask_mercure_sse import MercureSSE
from flask_mailman_templates import MailTemplates
from flask_suspense import Suspense, render_template, suspense_before_render_template, suspense_before_render_blocks
#from flask_observability import Observability
# 3rd party extensions
from flask_wtf.csrf import CSRFProtect
from flask_frozen import Freezer
from htmx_flask import Htmx
from flask_mailman import Mail
from flask_dramatiq import Dramatiq
from flask_debugtoolbar import DebugToolbarExtension
# from hyperflask
from .forms import Form
from .utils.page_actions import page_action_url
from .utils.htmx import htmx_oob, respond_with_flash_messages
from .utils.markdown import jinja_markdown, MarkdownExtension
from .utils.html import sanitize_html, nl2br
from .components import register_components
from .model import Model, File as SQLFileType
from .security import respond_with_security_headers, csp_nonce
from . import page_helpers
# others
from jinja_super_macros.registry import FileLoader
from jinja_wtforms.extractor import map_jinja_call_node_to_func
from sqlorm.sql_template import SQLTemplate
from periodiq import PeriodiqMiddleware
import os


map_jinja_call_node_to_func(_, "_")
map_jinja_call_node_to_func(_p, "_p")
map_jinja_call_node_to_func(_n, "_n")
map_jinja_call_node_to_func(_np, "_np")
map_jinja_call_node_to_func(lazy_gettext, "lazy_gettext")


class Hyperflask(Flask):
    config_class = Config

    def __init__(self, *args, static_mode="hybrid", instrument=False, layouts_folder="layouts",
                 emails_folder="emails", forms_folder="forms", assets_folder="assets", pages_folder="pages", migrations_folder="migrations",
                 config=None, config_filename="config.yml", database_uri="sqlite://:memory:", proxy_fix=True, **kwargs):

        super().__init__(*args, **kwargs)
        if proxy_fix:
            self.wsgi_app = ProxyFix(self.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

        self.config.update({
            "FREEZER_DESTINATION": os.path.join(self.root_path, "_site"),
            "FREEZER_STATIC_IGNORE": [],
            "WTF_CSRF_CHECK_DEFAULT": False,
            "OTEL_INSTRUMENT": instrument,
            "DRAMATIQ_BROKER": "dramatiq.brokers.redis:RedisBroker",
            "DEBUG_TB_INTERCEPT_REDIRECTS": False,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            # Hyperflask specific
            "LAYOUT": "layouts/default.html",
            "ALPINE": False,
            "STATIC_MODE": static_mode,
            "ASSETS_INCLUDE_ALPINE": False,
            "HTMX_EXT": [],
            "HTMX_BOOST_SITE": False,
            "MARKDOWN_OPTIONS": {"extensions": ["fenced_code", "nl2br", "attr_list", "admonition", "codehilite"]},
            "MARKDOWN_SANITIZER_CONFIG": {},
            "FLASH_TOAST_OOB": True,
            "FLASH_TOAST_REMOVE_AFTER": None,
            "SERVER_SECURED": False,
            "CSP_HEADER": True,
            "CSP_SAFE_SRC": ["'self'"],
            "CSP_UNSAFE_EVAL": True,
            "CSP_UNSAFE_INLINE": True,
            "CSP_FRAME_ANCESTORS": True,
            "CSP_FRAME_ANCESTORS_SAFE_ENDPOINTS": [],
            "REFERRER_POLICY": "strict-origin-when-cross-origin",
            "HSTS_HEADER": False
        })
        if config:
            self.config.update(config)
        if config_filename:
            self.config.load(config_filename)
        if self.debug:
            self.config.setdefault("MAIL_BACKEND", "console")

        self.config["PAGES_MARKDOWN_OPTIONS"] = self.config["MARKDOWN_OPTIONS"]
        self.config["COLLECTIONS_MARKDOWN_OPTIONS"] = self.config["MARKDOWN_OPTIONS"]
        self.config["MAIL_TEMPLATES_MARKDOWN_OPTIONS"] = self.config["MARKDOWN_OPTIONS"]

        if self.config['SERVER_SECURED']:
            self.config.update({
                'FORCE_URL_SCHEME': 'https',
                'PREFERRED_URL_SCHEME': 'https',
                'SESSION_COOKIE_SECURE': True,
                'REMEMBER_COOKIE_SECURE': True
            })
            self.config.setdefault("HSTS_HEADER", "max-age=31556926; includeSubDomains") # 1 year

        #self.otel = Observability(self)

        self.jinja_env.add_extension(LayoutExtension)
        self.jinja_env.add_extension(WtformExtension)
        self.jinja_env.add_extension(MarkdownExtension)
        self.jinja_env.filters.update(markdown=jinja_markdown, sanitize=sanitize_html, nl2br=nl2br)
        self.jinja_env.globals.update(page_action_url=page_action_url, app=self, csp_nonce=csp_nonce)
        self.jinja_env.form_base_cls = Form
        self.jinja_env.default_layout = self.config["LAYOUT"]
        self.forms = self.jinja_env.forms

        self.jinja_env.loader = ChoiceLoader([self.jinja_env.loader])
        if layouts_folder and os.path.exists(os.path.join(self.root_path, layouts_folder)):
            layout_loader = FileSystemLoader(os.path.join(self.root_path, layouts_folder))
            self.jinja_env.loader.loaders.append(PrefixLoader({os.path.basename(layouts_folder): layout_loader}))
        self.jinja_env.loader.loaders.extend([
            FileLoader(os.path.join(os.path.dirname(__file__), "layouts/web.html"), "layouts/default.html"),
            FileLoader(os.path.join(os.path.dirname(__file__), "layouts/web.html"), "layouts/base.html"),
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
        self.components = self.macros # alias
        Babel(self, extract_locale_from_request="locale")
        Geolocation(self)
        Files(self)
        MailTemplates(self, template_folder=emails_folder)
        file_routes = FileRoutes(self, pages_folder=pages_folder, module_view_class=HyperModuleView)
        self.page_helper = file_routes.page_helper
        self.collections = Collections(self)
        self.sse = MercureSSE(self)

        self.assets = AssetsPipeline(self, assets_folder=assets_folder, inline=True, include_inline_on_demand=False,
                                     inline_template_exts=[".html", ".jpy"], tailwind_expand_env_vars=True,
                                     tailwind_sources=[os.path.join(os.path.dirname(__file__), "ui")])
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
        self.assets.state.copy_files_from_node_modules.update({
            "bootstrap-icons/font": "bootstrap-icons"
        })
        self.assets.bundle(
            {"@hyperflask": ["app.js"],
             "@hyperflask/alpine": ["alpine-csp.js" if not self.config["CSP_UNSAFE_EVAL"] else "alpine.js"]},
            from_package="hyperflask",
            assets_folder="static"
        )
        self.assets.include("@hyperflask", 0)
        if self.config["ALPINE"]:
            self.assets.include("@hyperflask/alpine", 0)

        self.extensions['mail_templates'].jinja_env.add_extension(LayoutExtension)
        self.extensions['mail_templates'].jinja_env.default_layout = "layout.mjml"
        self.extensions['mail_templates'].loaders.extend([
            FileLoader(os.path.join(os.path.dirname(__file__), 'layouts/email.mjml'), 'layout.mjml'),
            FileLoader(os.path.join(os.path.dirname(__file__), 'layouts/email.mjml'), 'base_layout.mjml')
        ])

        self.macros.register_from_directory(os.path.join(os.path.dirname(__file__), "ui"))
        if hasattr(file_routes, "loader"):
            self.forms.register_from_loader(file_routes.loader, "pages")
        self.macros.create_from_func(htmx_oob, "HtmxOob", receive_caller=True, caller_alias="html")

        self.components_loader, _ = register_components(self)
        if self.components_loader:
            self.forms.register_from_loader(self.components_loader)

        if forms_folder and os.path.isdir(os.path.join(self.root_path, forms_folder)):
            for macro in self.macros.create_from_directory(os.path.join(self.root_path, forms_folder)):
                self.forms.register(self.macros.resolve_template(macro), macro)

        self.after_request(respond_with_security_headers)
        if self.config["FLASH_TOAST_OOB"]:
            self.after_request(respond_with_flash_messages)

        self.collections.register_freezer_generator(self.freezer)

        SQLTemplate.eval_globals.update(app=self)
        self.db = FlaskSQLORM(self, database_uri=database_uri, migrations_folder=migrations_folder)
        self.db.Model = Model
        self.db.File = SQLFileType

        Suspense(self, nonce_getter="csp_nonce()")

        @suspense_before_render_template.connect_via(self, weak=False)
        def on_suspense_before_render_template(sender, **kwargs):
            csp_nonce() # we will need a nonce but the first call will be after the template started rendering

        @suspense_before_render_blocks.connect_via(self, weak=False)
        def on_suspense_before_render_blocks(sender, **kwargs):
            return f'<script nonce="{csp_nonce()}">htmx.bootstrap()</script>'

        @self.errorhandler(404)
        def not_found(error):
            try:
                return render_template("404.html"), 404
            except TemplateNotFound:
                return self.make_response(("404 Not Found", 404))

        @self.errorhandler(500)
        def internal_server_error(error):
            try:
                return render_template("500.html"), 500
            except TemplateNotFound:
                return self.make_response(("500 Internal Server Error", 500))

    def relative_import_name(self, name):
        return f"{self.import_name}.{name}" if self.import_name != "__main__" else name


class HyperModuleView(ModuleView):
    def _render_template(self):
        return render_template(page.template)


def static(func):
    pass


def dynamic(func=None, static_template=None):
    def decorator(func):
        pass
    return decorator(func) if func else decorator
