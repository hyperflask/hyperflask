from flask_frozen import Freezer as FlaskFreezer
from pathlib import Path
from enum import Enum


class StaticMode(Enum):
    STATIC = "static"
    HYBRID = "hybrid"
    DYNAMIC = "dynamic"


class Freezer(FlaskFreezer):
    @property
    def root(self):
        return Path(self.app.config['FREEZER_DESTINATION'])

    def _check_endpoints(self, seen_endpoints):
        if StaticMode(self.app.config['STATIC_MODE']) != StaticMode.STATIC:
            return
        super()._check_endpoints(seen_endpoints)

    def urlpath_to_filepath(self, path):
        """Convert URL path like /admin/ to file path like admin/index.html."""
        if path.endswith('/'):
            path += 'index.html'
        # Remove the initial slash that should always be there
        assert path.startswith('/')
        if self.app.config.get('FREEZER_DEFAULT_FILE_EXTENSION') and '.' not in path.split('/')[-1]:
            path += f".{self.app.config['FREEZER_DEFAULT_FILE_EXTENSION']}"
        return path[1:]


def static(func=None, values=None):
    if func is None:
        return lambda f: static(f, values=values)
    func.__freezer__ = True
    func.__freezer_values__ = values
    return func


def dynamic(func):
    func.__freezer__ = False
    return func


def freezer_url_generator(app):
    """URL generator for URL rules that take no arguments."""
    for rule in app.url_map.iter_rules():
        if rule.arguments or 'GET' not in rule.methods:
            continue
        if rule.endpoint.startswith('mercure_hub'):
            continue
        if rule.endpoint in app.view_functions and not getattr(app.view_functions[rule.endpoint], '__freezer__', True):
            continue
        values = getattr(app.view_functions.get(rule.endpoint), '__freezer_values__', None) or {}
        yield rule.endpoint, values
