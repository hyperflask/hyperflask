from jinja2.ext import Extension
from jinja_super_macros import html_tag
from flask import current_app
from .resources import ResourceList, Resource


def reactive(obj, attr=None):
    if attr and hasattr(getattr(obj, attr), "__reactive__"):
        obj = getattr(obj, attr)
        attr = None
    elif not hasattr(obj, "__reactive__"):
        return getattr(obj, attr) if attr else obj
    
    current_app.assets.include("@hyperflask/reactive")

    mercure_topic, many = obj.__reactive__()
    
    if many:
        if attr:
            raise Exception("Cannot access attribute of a ResourceList")
        return html_tag("div", {"x-reactive-list": obj.resource.name})
    
    return html_tag("span", {"x-reactive-prop": obj.resource.name, "data-attr": attr})


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
                args = [obj, attr]
            else:
                args = [value]
            replacement = "{{ reactive(" + ", ".join(args) + ") }}"
            source = source[:pos] + replacement + source[end + 2:]
            pos = source.find("{!", pos + len(replacement) + 2)
        return source