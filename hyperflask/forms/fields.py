from . import widgets
from wtforms import fields


__all__ = ('StringField', 'PasswordField', 'EmailField')


class StringField(fields.StringField):
    widget = widgets.TextInput()


class PasswordField(fields.PasswordField):
    widget = widgets.PasswordInput()


class EmailField(fields.StringField):
    widget = widgets.EmailInput()
