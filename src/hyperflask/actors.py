from threading import local
from dramatiq import Middleware, actor
import importlib


DRAMATIQ_BROKERS = {
    "amqp": "dramatiq.brokers.rabbitmq:RabbitmqBroker",
    "redis": "dramatiq.brokers.redis:RedisBroker",
    "sqlite": "dramatiq_sqlite:SQLiteBroker",
}


def discover_broker(broker_cls=None, broker_url=None):
    if not broker_url and broker_cls and "://" in broker_cls:
        broker_url = broker_cls
        broker_cls = None
    if not broker_cls and broker_url:
        if "://" not in broker_url:
            broker_name = "sqlite"
        else:
            broker_name, broker_url = broker_url.split("://", 1)
        if broker_name not in DRAMATIQ_BROKERS:
            raise ValueError(f"Unknown dramatiq broker '{broker_name}'")
        broker_cls = DRAMATIQ_BROKERS[broker_name]
    if isinstance(broker_cls, str):
        module_name, cls_name = broker_cls.split(":")
        module = importlib.import_module(module_name)
        broker_cls = getattr(module, cls_name)
    return broker_cls, broker_url


def make_actor_decorator(app):
    def actor_decorator(**kw):
        def decorator(fn):
            if getattr(app, 'dramatiq_broker', None):
                kw['broker'] = app.dramatiq_broker
                return actor(**kw)(fn)
            return UndefinedBrokerActor(fn)
        return decorator
    return actor_decorator


class AppContextMiddleware(Middleware):
    # Setup Flask app for actor. Borrowed from
    # https://github.com/Bogdanp/flask_dramatiq_example.

    state = local()

    def __init__(self, app):
        self.app = app

    def before_process_message(self, broker, message):
        context = self.app.app_context()
        context.push()

        self.state.context = context

    def after_process_message(
            self, broker, message, *, result=None, exception=None):
        try:
            context = self.state.context
            context.pop(exception)
            del self.state.context
        except AttributeError:
            pass

    after_skip_message = after_process_message


class UndefinedBrokerActor:
    def __init__(self, fn):
        self.fn = fn
        self.__name__ = fn.__name__

    def __call__(self, *args, **kwargs):
        return self.fn(*args, **kwargs)

    def send(self, *args, **kwargs):
        raise RuntimeError("No broker defined for Dramatiq actors.")

    def send_with_options(self, *args, **kwargs):
        raise RuntimeError("No broker defined for Dramatiq actors.")
