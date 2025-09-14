from . import widgets
from wtforms import fields


__all__ = ('BooleanField', 'DateField', 'DateTimeField', 'DateTimeLocalField',
           'DecimalField', 'DecimalRangeField', 'EmailField', 'FileField',
           'MultipleFileField', 'FloatField', 'IntegerField', 'IntegerRangeField',
           'MonthField', 'RadioField', 'SelectField', 'SearchField',
           'SelectMultipleField', 'StringField', 'TelField', 'TimeField',
           'URLField', 'PasswordField', 'TextAreaField', 'ColorField')


def create_field_class(basecls, widget, attr='widget'):
    return type(basecls.__name__, (basecls,), {attr: widget})


BooleanField = create_field_class(fields.BooleanField, widgets.CheckboxInput())
DateField = create_field_class(fields.DateField, widgets.DateInput())
DateTimeField = create_field_class(fields.DateTimeField, widgets.DateTimeInput())
DateTimeLocalField = create_field_class(fields.DateTimeLocalField, widgets.DateTimeLocalInput())
DecimalField = create_field_class(fields.DecimalField, widgets.NumberInput(step="any"))
DecimalRangeField = create_field_class(fields.DecimalRangeField, widgets.RangeInput(step="any"))
EmailField = create_field_class(fields.EmailField, widgets.EmailInput())
FileField = create_field_class(fields.FileField, widgets.FileInput())
MultipleFileField = create_field_class(fields.MultipleFileField, widgets.FileInput(multiple=True))
FloatField = create_field_class(fields.FloatField, widgets.TextInput())
IntegerField = create_field_class(fields.IntegerField, widgets.NumberInput())
IntegerRangeField = create_field_class(fields.IntegerRangeField, widgets.RangeInput())
MonthField = create_field_class(fields.MonthField, widgets.MonthInput())
RadioField = create_field_class(fields.RadioField, widgets.RadioInput(), 'option_widget')
SelectField = create_field_class(fields.SelectField, widgets.Select())
SearchField = create_field_class(fields.SearchField, widgets.SearchInput())
SelectMultipleField = create_field_class(fields.SelectMultipleField, widgets.Select(multiple=True))
StringField = create_field_class(fields.StringField, widgets.TextInput())
TelField = create_field_class(fields.TelField, widgets.TelInput())
TimeField = create_field_class(fields.TimeField, widgets.TimeInput())
URLField = create_field_class(fields.URLField, widgets.URLInput())
PasswordField = create_field_class(fields.PasswordField, widgets.PasswordInput())
TextAreaField = create_field_class(fields.TextAreaField, widgets.TextArea())
ColorField = create_field_class(fields.ColorField, widgets.ColorInput())
