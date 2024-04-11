from flask import request, url_for
from flask_file_routes import page
import inspect


def page_action(func=None, name=None):
    def decorator(func):
        action_name = func.__name__[3:] if not name else name
        if request.method != "POST" or request.args.get("__action") != action_name:
            return
        sig = inspect.signature(func)
        args = {}
        for param in sig.parameters:
            args[param.name] = request.values.get(param)
        rv = func(**args)
        page.respond(rv or ("", 200))
    return decorator(func) if func else decorator


def page_action_url(action, endpoint=None, **kwargs):
    return url_for(endpoint or request.endpoint, __action=action, **kwargs)


def hx_page_action(action, **kwargs):
    return 'hx-post="%s"' % page_action_url(action, **kwargs)