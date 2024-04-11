from wtforms import widgets


def create_input_class(basecls):
    class Input(basecls):
        def __call__(self, field, **kwargs):
            extend_class(kwargs, "input input-bordered w-full")
            return super().__call__(field, **kwargs)
    return Input


TextInput = create_input_class(widgets.TextInput)
PasswordInput = create_input_class(widgets.PasswordInput)
EmailInput = create_input_class(widgets.EmailInput)


def extend_class(kwargs, classes):
    c = kwargs.pop('class', '') or kwargs.pop('class_', '')
    kwargs['class'] = '%s %s' % (classes, c)
