import markdown
from markupsafe import Markup
import jinja2
from jinja2.ext import Extension
from flask import current_app
from .html import sanitize_html


def render_markdown(input, safe=True, sanitize_config=None):
    html = markdown.markdown(input, **current_app.config.get("MARKDOWN_OPTIONS", {}))
    if safe:
        sanitize_config = dict(current_app.config.get("MARKDOWN_SANITIZER_CONFIG", {}), **(sanitize_config or {}))
        return sanitize_html(html, **sanitize_config)
    return html


def jinja_markdown(input, **kwargs):
    return Markup(render_markdown(input, **kwargs))


class MarkdownExtension(Extension):
    tags = {"markdown"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(["name:endmarkdown"], drop_needle=True)
        return jinja2.nodes.CallBlock(
            self.call_method("render_markdown"), [], [], body
        ).set_lineno(lineno)

    def render_markdown(self, caller):
        return render_markdown(caller()).strip()
