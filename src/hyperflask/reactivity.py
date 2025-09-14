from jinja2.ext import Extension
from jinja_super_macros import html_tag
from flask import current_app
from flask_mercure_sse import mercure_hub_url
from markupsafe import Markup
from collections import namedtuple


ReactiveInfo = namedtuple("ReactiveInfo", ["topic", "events", "render", "html_attrs", "tagname"], defaults=[None, None, None, "hf-reactive"])


def reactive(obj, attr=None):
    if attr and hasattr(getattr(obj, attr), "__reactive__"):
        obj = getattr(obj, attr)
        attr = None
    elif not hasattr(obj, "__reactive__"):
        return getattr(obj, attr) if attr else obj
    info = ReactiveInfo(*obj.__reactive__(attr))
    return render_reactive(info, getattr(obj, attr) if attr else obj)


def render_reactive(info, default_value=""):
    html_attrs = info.html_attrs or {}
    html_attrs.setdefault("mercure-url", mercure_hub_url())
    if info.topic:
        html_attrs.setdefault("topic", info.topic)
    if info.events:
        html_attrs.setdefault("events", ",".join(info.events))
    return html_tag(info.tagname, html_attrs) + (info.render() if info.render else default_value) + Markup(f"</{info.tagname}>")


class ReactiveExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals["reactive"] = reactive

    def preprocess(self, source, name, filename=None):
        pos = source.find("{!")
        while pos >= 0:
            end = source.find("!}", pos)
            if end < 0:
                raise Exception("Missing closing bracket for reactive")
            value = source[pos + 2:end]
            if "." in value:
                obj, attr = value.rsplit(".", 1)
                args = [obj, f'"{attr}"']
            else:
                args = [value]
            replacement = "{{ reactive(" + ", ".join(args) + ") }}"
            source = source[:pos] + replacement + source[end + 2:]
            pos = source.find("{!", pos + len(replacement) + 2)
        return source
