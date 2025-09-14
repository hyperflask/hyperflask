from htmx_flask import request
from htmx_flask import make_response
from markupsafe import Markup
import re


def htmx_redirect(url):
    return make_response(redirect=url)


def htmx_oob(html, swap="outerHTML", target=None, wrap=True):
    if not request.htmx:
        return ""
    if callable(html):
        html = html()
    swap_oob = f"{swap}:{target}" if target else swap
    html = str(html).strip()
    m = re.match(r'<([a-z\-0-9]+)', html, re.I)
    if swap != "outerHTML" and wrap:
        wrap_tag = wrap if wrap is not True else {"tr": "table", "li": "ul"}.get(m.group(1).lower() if m else None, "div")
        html = f"<{wrap_tag} hx-swap-oob=\"{swap_oob}\">{html}</{wrap_tag}>"
    elif m:
        tag, html = html.split(" ", 1)
        html = f"{tag} hx-swap-oob=\"{swap_oob}\" {html}"
        if wrap and tag[1:].lower() in ("tr", "td", "th", "thead", "tbody", "tfoot", "colgroup", "caption", "col"):
            html = f"<template>{html}</template>"
    return Markup(html)
