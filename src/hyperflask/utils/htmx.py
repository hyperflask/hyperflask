from htmx_flask import request
from htmx_flask import make_response
from markupsafe import Markup
from flask import get_flashed_messages, current_app, json
import re


def htmx_redirect(url):
    return make_response(redirect=url)


def htmx_oob(html, swap="outerHTML", target=None, wrap=True):
    if callable(html):
        html = html()
    swap_oob = f"{swap}:{target}" if target else swap
    html = str(html).strip()
    if swap != "outerHTML" and wrap:
        # htmx inserts the content of the wrapper (template content can hold any element, eg. table rows)
        wrap_tag = wrap if wrap is not True else "template"
        html = f"<{wrap_tag} hx-swap-oob=\"{swap_oob}\">{html}</{wrap_tag}>"
    else:
        html = re.sub(r'^<([a-z\-0-9]+)', lambda m: f'<{m.group(1)} hx-swap-oob="{swap_oob}"', html, count=1, flags=re.I)
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
    response.headers["HX-Trigger"] = json.dumps(trigger)
    return response


def respond_with_flash_messages(response, only_if_htmx=True, target="#flash-messages-toast"):
    if only_if_htmx and not request.htmx:
        return response

    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        props = {"category": category, "caller": lambda: message}
        if current_app.config["FLASH_TOAST_REMOVE_AFTER"]:
            props["remove-me"] = current_app.config["FLASH_TOAST_REMOVE_AFTER"]
        messages.append(htmx_oob(current_app.macros.FlashMessage(**props), swap="afterbegin", target=target))

    response.set_data("\n".join(messages) + response.get_data(as_text=True))
    return response
