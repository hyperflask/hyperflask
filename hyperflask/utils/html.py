from html_sanitizer import Sanitizer
from markupsafe import Markup
from flask import current_app


def sanitize_html(html, **config):
    config = dict(current_app.config.get("HTML_SANITIZER_CONFIG", {}), **config)
    sanitizer = Sanitizer(config)
    return Markup(sanitizer.sanitize(html))


def nl2br(value):
    return value.replace("\n", "<br>")
