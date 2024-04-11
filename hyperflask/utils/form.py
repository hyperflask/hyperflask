from flask_wtf import FlaskForm
from flask import abort
from wtforms.csrf.core import CSRFTokenField


class Form(FlaskForm):
    def validate_or_400(self):
        if not self.validate():
            abort(400)

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if not isinstance(field, CSRFTokenField):
                field.populate_obj(obj, name)

    @property
    def data(self):
        return {name: f.data for name, f in self._fields.items() if not isinstance(f, CSRFTokenField)}
    
    def data_without(self, *fields):
        return {name: f.data for name, f in self._fields.items() if name not in fields and not isinstance(f, CSRFTokenField)}