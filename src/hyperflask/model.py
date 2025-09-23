from flask import current_app
from flask_sqlorm import Model as BaseModel
from flask_files import save_file, File
from sqlorm.resultset import CompositeResultSet
from sqlorm import SQLType
from markupsafe import Markup
import abc


File = SQLType("text", save_file, File.from_uri)


class ModelResultSet(CompositeResultSet):
    def __str__(self):
        return Markup("".join([str(item) for item in self]))


class ModelMercureTopic:
    def __init__(self, topic=None, topic_per_obj=True):
        self.topic = topic
        self.topic_per_obj = topic_per_obj

    def __get__(self, instance, owner):
        if instance and self.topic_per_obj:
            if isinstance(self.topic_per_obj, str):
                id = getattr(instance, self.topic_per_obj)
            else:
                id = owner.__mapper__.get_primary_key(instance)
            return f"{self.topic or owner.__name__}/{id}"
        return self.topic or owner.__name__


class Model(BaseModel, abc.ABC):
    __resultset_class__ = ModelResultSet
    __macro__ = None
    __mercure_sse_topic__ = ModelMercureTopic()

    def __mercure_sse_data__(self):
        return str(self)

    def __str__(self):
        if not self.__macro__:
            return repr(self)

        macro = self.__macro__
        prop = "obj"
        if "(" in macro:
            macro, prop = macro.rstrip(")").rsplit("(")

        props = {prop: self} if prop else {}
        return Markup(current_app.macros[macro](**props))
