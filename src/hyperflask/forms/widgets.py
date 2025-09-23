from wtforms import widgets


def create_widget_class(basecls, cssclass="input"):
    class Input(basecls):
        def __call__(self, field, **kwargs):
            extend_class(kwargs, cssclass)
            kwargs = {k.replace('_', '-'): v for k, v in kwargs.items() if v is not None}
            return super().__call__(field, **kwargs)
    return Input


ColorInput = create_widget_class(widgets.ColorInput)
CheckboxInput = create_widget_class(widgets.CheckboxInput, "checkbox")
DateTimeInput = create_widget_class(widgets.DateTimeInput)
DateTimeLocalInput = create_widget_class(widgets.DateTimeLocalInput)
DateInput = create_widget_class(widgets.DateInput)
EmailInput = create_widget_class(widgets.EmailInput)
FileInput = create_widget_class(widgets.FileInput, "file-input")
MonthInput = create_widget_class(widgets.MonthInput)
NumberInput = create_widget_class(widgets.NumberInput)
PasswordInput = create_widget_class(widgets.PasswordInput)
RadioInput = create_widget_class(widgets.RadioInput, "radio")
RangeInput = create_widget_class(widgets.RangeInput, "range")
SearchInput = create_widget_class(widgets.SearchInput)
Select = create_widget_class(widgets.Select, "select")
TelInput = create_widget_class(widgets.TelInput)
TextArea = create_widget_class(widgets.TextArea, "textarea")
TextInput = create_widget_class(widgets.TextInput)
TimeInput = create_widget_class(widgets.TimeInput)
URLInput = create_widget_class(widgets.URLInput)
WeekInput = create_widget_class(widgets.WeekInput)


def extend_class(kwargs, classes):
    c = kwargs.pop('class', '') or kwargs.pop('class_', '')
    kwargs['class'] = '%s %s' % (classes, c)
