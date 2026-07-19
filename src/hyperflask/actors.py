from threading import local
import typing as t
import importlib
from datetime import timedelta
from dramatiq import Middleware, actor as register_actor, Message
from flask import has_app_context, current_app
from sqlorm.helpers import after_commit as sqlorm_after_commit


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


class actor:
    @classmethod
    def bind(cls, broker):
        return type('bound_actor', (cls,), {'__broker__': broker})

    def __init__(self, *args, **kwargs):
        self.actor_args = (args, kwargs)
        self.fn = None
        self.actor = None

    def __call__(self, *args, **kwargs):
        if not self.fn:
            self.fn = args[0]
            if getattr(self, '__broker__', None):
                self.register(self.__broker__)
            elif has_app_context() and getattr(current_app, 'dramatiq_broker', None):
                self.register(current_app.dramatiq_broker)
            return self
        return self.fn(*args, **kwargs)

    def register(self, broker):
        self.actor = register_actor(broker=broker, *self.actor_args[0], **self.actor_args[1])(self.fn)

    def __getattr__(self, name):
        if self.actor:
            return getattr(self.actor, name)
        raise AttributeError(name)

    def send(self, *args, **kwargs):
        return self.send_with_options(args=args, kwargs=kwargs)

    def send_with_options(
        self,
        *,
        args: tuple = (),
        kwargs: t.Optional[dict[str, t.Any]] = None,
        delay: t.Optional[timedelta | int] = None,
        after_commit: bool = True,
        **options,
    ) -> Message:
        if not self.actor:
            raise RuntimeError("No broker defined for Dramatiq actors.")

        if isinstance(delay, timedelta):
            delay = int(delay.total_seconds() * 1000)

        message = self.actor.message_with_options(args=args, kwargs=kwargs, **options)

        if after_commit:
            sqlorm_after_commit(lambda: self.actor.broker.enqueue(message, delay=delay))
            return message

        return self.actor.broker.enqueue(message, delay=delay)


class ActorGroup(list):
    def actor(self, *args, **kwargs):
        def decorator(fn):
            a = actor(*args, **kwargs)(fn)
            self.append(a)
            return a
        return decorator

    def register(self, broker):
        for a in self:
            a.register(broker)


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
