from htmx_flask import request
from htmx_flask import make_response
from markupsafe import Markup
import re


def htmx_redirect(url):
    return make_response(redirect=url)


def htmx_oob(html, swap="outerHTML", target=None):
    if not request.htmx:
        return ""
    if callable(html):
        html = html()
    if target:
        swap = f"{swap}:{target}"
    html = str(html).strip()
    if re.match(r'<([a-z]+)', html, re.I):
        tag, html = html.split(" ", 1)
        html = f"{tag} hx-swap-oob=\"{swap}\" {html}"
        if tag[1:].lower() in ("tr", "td", "th", "thead", "tbody", "tfoot", "colgroup", "caption", "col"):
            html = f"<template>{html}</template>"
    return Markup(html)
