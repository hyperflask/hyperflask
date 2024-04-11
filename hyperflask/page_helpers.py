from flask_file_routes import DEFAULT_HELPERS
from flask import g, current_app
from .utils.page_actions import page_action


def csrf_protect(page):
    current_app.csrf.protect()


def forms(page):
    return current_app.forms[page.template]


def form(page):
    def form_helper(template=None, **kwargs):
        page.form = current_app.forms[template or page.template](**kwargs)
        return page.form
    return form_helper


def stream(page):
    g.__page_stream__ = True
    return


def action(page):
    def decorator(func=None, name=None):
        return page_action(func, name)
    return decorator


DEFAULT_HELPERS.update(csrf_protect=csrf_protect,
                       forms=forms,
                       form=form,
                       stream=stream,
                       action=action)