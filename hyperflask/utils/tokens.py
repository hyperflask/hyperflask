from flask import current_app, abort
from werkzeug.local import LocalProxy
from itsdangerous import URLSafeTimedSerializer, BadSignature


def get_token_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


token_serializer = LocalProxy(get_token_serializer)


def create_token(data, **serializer_kwargs):
    return token_serializer.dumps(data, **serializer_kwargs)


def load_token(token, **serializer_kwargs):
    try:
        return token_serializer.loads(token, **serializer_kwargs)
    except BadSignature:
        return None


def load_token_or_404(token, **serializer_kwargs):
    data = load_token(token)
    if data is None:
        abort(404)
    return data