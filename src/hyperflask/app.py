# flask
from flask import Flask, has_request_context, request
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader, TemplateNotFound
from werkzeug.middleware.proxy_fix import ProxyFix
# hyperflask extensions
from jinja_layout import LayoutExtension
from jinja_wtforms import WtformExtension
from flask_assets_pipeline import AssetsPipeline, asset_url, static_url
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
from flask_suspense import Suspense, render_template, suspense_before_render_template, suspense_before_render_macros
#from flask_observability import Observability
# 3rd party extensions
from flask_wtf.csrf import CSRFProtect
from htmx_flask import Htmx
from flask_mailman import Mail
from flask_debugtoolbar import DebugToolbarExtension
# from hyperflask
from .forms import Form
from .utils.page_actions import page_action_url
from .utils.htmx import htmx_oob, respond_with_flash_messages
from .utils.markdown import jinja_markdown, MarkdownExtension
from .utils.html import sanitize_html, nl2br
from .utils.metadata import metadata_tags
from .utils.freezer import StaticMode, Freezer, freezer_url_generator
from .utils.image import image_tag
from .components import register_components
from .model import Model, File as SQLFileType, UndefinedDatabase
from .actors import AppContextMiddleware, discover_broker, make_actor_decorator
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

    def __init__(self, *args, static_mode=StaticMode.DYNAMIC, instrument=False, layouts_folder="layouts",
                 emails_folder="emails", forms_folder="forms", assets_folder="assets", pages_folder="pages", migrations_folder="migrations",
                 config=None, config_filename="config.yml", database_uri=None, proxy_fix=True, **kwargs):

        super().__init__(*args, **kwargs)
        if proxy_fix:
            self.wsgi_app = ProxyFix(self.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

        self.config.update({
            "FREEZER_DESTINATION": "_site",
            "FREEZER_STATIC_IGNORE": [],
            "FREEZER_IGNORE_404_NOT_FOUND": True,
            "FREEZER_IGNORE_MIMETYPE_WARNINGS": True,
            "FREEZER_REDIRECT_POLICY": "ignore",
            "FREEZER_DEFAULT_FILE_EXTENSION": "html",
            "WTF_CSRF_CHECK_DEFAULT": False,
            "OTEL_INSTRUMENT": instrument,
            "DEBUG_TB_INTERCEPT_REDIRECTS": False,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SQLORM_URI": database_uri,
            # Hyperflask specific
            "URL_FOR_SERVER_NAME": None,
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
            "HSTS_HEADER": False,
            "IMAGES_DEFAULT_LOADING": "lazy",
            "IMAGES_DEFAULT_DECODING": "async",
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

        if not self.debug and not self.testing and not self.config.get('MERCURE_HUB_URL'):
            self.config['MERCURE_HUB_URL'] = "http://localhost:5300/.well-known/mercure"
            self.config.setdefault('MERCURE_PUBLIC_HUB_URL', True)

        #self.otel = Observability(self)

        self.jinja_env.add_extension(LayoutExtension)
        self.jinja_env.add_extension(WtformExtension)
        self.jinja_env.add_extension(MarkdownExtension)
        self.jinja_env.filters.update(markdown=jinja_markdown,
                                      sanitize=sanitize_html,
                                      nl2br=nl2br)
        self.jinja_env.globals.update(page_action_url=page_action_url,
                                      app=self,
                                      csp_nonce=csp_nonce,
                                      metadata_tags=metadata_tags)
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
        self.freezer = Freezer(self, with_no_argument_rules=False, log_url_for=self.config.get('FREEZER_LOG_URL_FOR', False))
        self.freezer.register_generator(lambda: freezer_url_generator(self))
        self.csrf = CSRFProtect(self)
        Htmx(self)
        Mail(self)

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
        self.macros.create_from_func(image_tag, "Image")

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

        if self.config.get('SQLORM_URI'):
            SQLTemplate.eval_globals.update(app=self)
            self.db = FlaskSQLORM(self, migrations_folder=migrations_folder)
            self.db.Model = Model
            self.db.File = SQLFileType
        else:
            self.db = UndefinedDatabase()

        broker_cls, broker_url = discover_broker(self.config.get('DRAMATIQ_BROKER'), self.config.get('DRAMATIQ_BROKER_URL'))
        if broker_cls:
            self.dramatiq_broker = broker_cls(url=broker_url)
            self.dramatiq_broker.add_middleware(AppContextMiddleware(self))
            self.dramatiq_broker.add_middleware(PeriodiqMiddleware())
        self.actor = make_actor_decorator(self)

        Suspense(self, nonce_getter="csp_nonce()")

        @suspense_before_render_template.connect_via(self, weak=False)
        def on_suspense_before_render_template(sender, **kwargs):
            csp_nonce() # we will need a nonce but the first call will be after the template started rendering

        @suspense_before_render_macros.connect_via(self, weak=False)
        def on_suspense_before_render_macros(sender, **kwargs):
            return ""
            return f'<script nonce="{csp_nonce()}">htmx.bootstrap()</script>' # waiting on PR 3441

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

    @property
    def base_url(self):
        scheme = self.config.get('PREFERRED_URL_SCHEME', 'http')
        if self.config.get('SERVER_NAME'):
            return f"{scheme}://{self.config['SERVER_NAME']}"
        if self.config['URL_FOR_SERVER_NAME']:
            return f"{scheme}://{self.config['URL_FOR_SERVER_NAME']}"
        if has_request_context():
            return request.host_url
        raise RuntimeError("No request context and no SERVER_NAME or URL_FOR_SERVER_NAME configured, cannot determine base_url")

    def url_for(self, *args, **kwargs):
        _external = kwargs.get("_external", False)
        _scheme = kwargs.get("_scheme", None)
        if _external and self.config['URL_FOR_SERVER_NAME']:
            # we handle the host and scheme ourselves
            kwargs['_external'] = False
            kwargs.pop('_scheme', None)
        else:
            _external = False
        url = super().url_for(*args, **kwargs)
        if not _external:
            return url
        if not _scheme:
            _scheme = self.config.get('PREFERRED_URL_SCHEME', 'http')
        url = f"{_scheme}://{self.config['URL_FOR_SERVER_NAME']}{url}"
        return url


class HyperModuleView(ModuleView):
    module_globals = dict(ModuleView.module_globals, asset_url=asset_url, static_url=static_url)

    def _render_template(self):
        return render_template(page.template)
