from htmx_flask import request
from htmx_flask import make_response
from markupsafe import Markup
from flask import get_flashed_messages, current_app, json
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


def respond_with_htmx_oob(response, html, **kwargs):
    response.set_data(htmx_oob(html, **kwargs) + response.get_data(as_text=True))
    return response


def add_hx_trigger(response, event, data=None):
    if "HX-Trigger" not in response.headers:
        trigger = json.dumps({event: data}) if data is not None else event
        response.headers["HX-Trigger"] = trigger
        return response

    trigger = response.headers["HX-Trigger"]
    if trigger.startswith("{"):
        trigger = json.loads(trigger)
    else:
        trigger = {trigger: None}
    trigger[event] = data
    response.headers["HX-Trigger"] = trigger
    return response


def respond_with_flash_messages(response, only_if_htmx=True, target="#flash-messages-toast"):
    if only_if_htmx and not request.htmx:
        return response

    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        props = {"category": category, "caller": lambda: message}
        if current_app.config["FLASH_TOAST_REMOVE_AFTER"]:
            props["remove-me"] = current_app.config["FLASH_TOAST_REMOVE_AFTER"]
        messages.append(htmx_oob(current_app.macros.FlashMessage(**props), swap="beforestart", target=target))

    response.set_data("\n".join(messages) + response.get_data(as_text=True))
    return response
