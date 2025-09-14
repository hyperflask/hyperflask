from wtforms import validators, ValidationError
from wtforms.fields import *
from wtforms.csrf.core import CSRFTokenField
from flask_wtf import FlaskForm
from flask import abort, flash as flask_flash
from jinja_wtforms.form import TEMPLATE_FORM_FIELDS
from .fields import *
from flask_wtf.file import FileField, MultipleFileField


TEMPLATE_FORM_FIELDS.update({
    "checkbox": BooleanField,
    "decimal": DecimalField,
    "date": DateField,
    "datetime": DateTimeField,
    "float": FloatField,
    "int": IntegerField,
    "radio": RadioField,
    "select": SelectField,
    "selectmulti": SelectMultipleField,
    "text": StringField,
    "textarea": TextAreaField,
    "password": PasswordField,
    "hidden": HiddenField,
    "datetimelocal": DateTimeLocalField,
    "decimalrange": DecimalRangeField,
    "email": EmailField,
    "intrange": IntegerRangeField,
    "search": SearchField,
    "tel": TelField,
    "url": URLField,
    "file": FileField,
    "files": MultipleFileField
})


class Form(FlaskForm):
    def validate_or_400(self, flash=None, flash_category="error"):
        if not self.validate():
            if isinstance(flash, str):
                flask_flash(flash, flash_category)
            elif flash:
                for field, errors in self.errors.items():
                    for error in errors:
                        flask_flash(f"{field}: {error}", flash_category)
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
