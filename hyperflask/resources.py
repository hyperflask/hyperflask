from hyperflask import db
from sqlorm import Model
from flask_apispec import marshal_with, use_args
from flask_apispec.views import MethodResource
from werkzeug.exceptions import HTTPException
import typing as t


class ResourceMeta(type):
    def __new__(cls, name, bases, attrs):
        cls = super().__new__(cls, name, bases, attrs)
        if not bases:
            return cls

        if not hasattr(cls, "schema"):
            cls.schema = create_model_schema(cls.model)

        return cls
    

def create_model_schema(model):
    pass


class ResourceError(HTTPException):
    def __init__(self, description, code=400):
        super().__init__(description)
        self.code = code


class ResourceNotFound(ResourceError):
    def __init__(self):
        super().__init__("URL not found", 404)


class Resource(metaclass=ResourceMeta):
    model: t.ClassVar[Model]
    url_prefix = None
    object_url_prefix = "/<id>"
    expose_create = True
    expose_edit = True
    expose_methods = t.ClassVar[t.Sequence[str]]

    @classmethod
    def list(cls):
        return ResourceList(cls, cls.model.find_all())

    @classmethod
    def create(cls, **kwargs):
        with db:
            return cls(cls.model.create(**kwargs))

    @classmethod
    def get(cls, id):
        obj = cls.model.get(id)
        if not obj:
            raise ResourceNotFound()
        return cls(obj)
    
    def __init__(self, obj):
        self.obj = obj

    def update(self, data):
        with db:
            self.obj.update(**data)

    def delete(self):
        with db:
            self.obj.delete()

    def __getattr__(self, name):
        return getattr(self.obj, name)
    
    def __reactive__(self):
        return

    @classmethod
    def register(cls, app, url_prefix="", endpoint_prefix=""):
        from .api import create_view_func

        @marshal_with(cls.schema(many=True))
        def many_get():
            return cls.list()
        
        @use_args(cls.schema)
        @marshal_with(cls.schema)
        def many_post(data):
            return cls.create(**data)
        
        @marshal_with(cls.schema)
        def single_get(id):
            return cls.get(id)
        
        @use_args(cls.schema)
        @marshal_with(cls.schema)
        def single_put(data, id):
            obj = cls.get(id)
            obj.update(data)
            return obj
        
        def single_delete(id):
            obj = cls.get(id)
            obj.delete()
            return {}, 204
        
        many_methods = {"get": many_get}
        if cls.expose_create:
            many_methods["post"] = many_post
        many_view = type(f"{cls.__name__}ManyView", (MethodResource,), many_methods)
        many_endpoint = endpoint_prefix + cls.__name__.lower() + "_many"

        single_methods = {"get": single_get}
        if cls.expose_edit:
            single_methods.update({"put": single_put, "delete": single_delete})
        single_view = type(f"{cls.__name__}View", (MethodResource,), single_methods)
        single_endpoint = endpoint_prefix + cls.__name__.lower()

        app.add_url_rule(url_prefix + cls.url_prefix, view_func=many_view.as_view(many_endpoint))
        app.add_url_rule(url_prefix + cls.url_prefix + cls.object_url_prefix, view_func=single_view.as_view(single_endpoint))

        endpoints = [many_endpoint, single_endpoint]

        for attr in dir(cls):
            if hasattr(getattr(cls, attr), "__expose__"):
                rule, endpoint, kwargs = getattr(cls, attr).__expose__
                view_func = create_view_func(getattr(cls, attr))
                app.add_url_rule(url_prefix + cls.url_prefix + rule, endpoint_prefix + endpoint, view_func=view_func, **kwargs)
                endpoints.append(endpoint_prefix + endpoint)

        return endpoints


def expose(rule=None, endpoint=None, **kwargs):
    def decorator(func):
        func.__expose__ = (rule or func.__name__, endpoint or func.__name__, kwargs)
        return func
    return decorator


class ResourceList:
    def __init__(self, resource_class, objects):
        self.resource_class = resource_class
        self.objects = objects

    def __iter__(self):
        return [self.resource_class(obj) for obj in self.objects]
    
    def __reactive__(self):
        return