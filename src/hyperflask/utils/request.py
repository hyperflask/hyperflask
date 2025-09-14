from flask import request
from urllib.parse import urlparse, urljoin
import functools


def is_safe_redirect_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )


def marshal_with_depends(content_types):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            response.headers["Content-Type"] = content_types
            return response

        return wrapper

    return decorator