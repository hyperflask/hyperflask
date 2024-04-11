import flask_apispec
from flask_apispec.extension import FlaskApiSpec
from flask_apispec.annotations import activate
import functools
import inspect
from .resources import Resource


class Api:
    def __init__(self, app, version="v1", **kwargs):
        self.url_prefix = f"/api/{version}"
        self.endpoint_prefix = f"api_{version}_"
        kwargs.setdefault("url_prefix", self.url_prefix)
        kwargs.setdefault("spec_url", "/spec.json")
        kwargs.setdefault("doc_url", "/")
        self.app = app
        self.docs = FlaskApiSpec(app, version=version, **kwargs)
        self.spec = self.docs.spec

    def expose(self, rule, endpoint=None, **kwargs):
        def decorator(target):
            nonlocal endpoint
            if inspect.isclass(target) and issubclass(target, Resource):
                for e in target.register(self.app, self.url_prefix, self.endpoint_prefix + (endpoint or "")):
                    self.docs.register(self.app.view_functions[e], endpoint=e)
            else:
                view_func = create_view_func(target)
                endpoint = self.endpoint_prefix + (endpoint or view_func.__name__)
                self.app.add_url_rule(self.url_prefix + rule, endpoint, view_func, **kwargs)
                self.docs.register(view_func, endpoint)
            return target
        return decorator

    @staticmethod
    def args(*args, **kwargs):
        kwargs["activate"] = False
        return flask_apispec.use_args(*args, **kwargs)

    @staticmethod
    def kwargs(*args, **kwargs):
        kwargs["activate"] = False
        return flask_apispec.use_kwargs(*args, **kwargs)

    @staticmethod
    def marshal_with(*args, **kwargs):
        kwargs["activate"] = False
        return flask_apispec.marshal_with(*args, **kwargs)


def create_view_func(func):
    @functools.wraps(func)
    def view_func(*args, **kwargs):
        return func(*args, **kwargs)
    if hasattr(func, "__apispec__"):
        view_func.__apispec__ = func.__apispec__
        func.view_func = activate(view_func)
    return view_func