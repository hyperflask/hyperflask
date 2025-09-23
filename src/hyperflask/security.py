from flask import request, current_app, g
from urllib.parse import urlparse, urljoin
import secrets


def is_safe_redirect_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )


def respond_with_security_headers(response):
    if current_app.config["CSP_HEADER"] is not False:
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = generate_csp_policy()

    if current_app.config['HSTS_HEADER']:
        response.headers['Strict-Transport-Security'] = current_app.config['HSTS_HEADER']

    if current_app.config['REFERRER_POLICY']:
        response.headers['Referrer-Policy'] = current_app.config['REFERRER_POLICY']

    return response


def generate_csp_policy():
    policy = current_app.config["CSP_HEADER"]
    if policy is True:
        policy = {
            "default-src": "'safe-src'",
            "manifest-src": "'self'",
            "connect-src": 'https: wss:' if current_app.config['SERVER_SECURED'] else 'http: ws:',
            "img-src": "* data: blob:",
            "media-src": "* data: blob:",
            "frame-src": "* data: blob:",
            "object-src": "* data: blob:"
        }
    policy.setdefault("script-src", policy["default-src"])
    policy.setdefault("style-src", policy["default-src"])

    if not current_app.config['CSP_FRAME_ANCESTORS']:
        policy["frame-ancestors"] = "'none'"
    elif isinstance(current_app.config['CSP_FRAME_ANCESTORS'], (list, tuple)):
        frame_ancestors = list(current_app.config['CSP_FRAME_ANCESTORS'])
        add_frame_ancestors = True
        for endpoint in current_app.config['CSP_FRAME_ANCESTORS_SAFE_ENDPOINTS']:
            ancestors = []
            if isinstance(endpoint, (list, tuple)):
                endpoint, ancestors = endpoint
            if request.endpoint == endpoint:
                if ancestors:
                    frame_ancestors.extend(ancestors)
                else:
                    add_frame_ancestors = False
                break
        if add_frame_ancestors:
            policy["frame-ancestors"] = ' '.join(set(frame_ancestors))

    if current_app.config.get('CSP_UNSAFE_EVAL'):
        policy["script-src"] += " 'unsafe-eval'"

    unsafe_inline = current_app.debug or current_app.config.get('CSP_UNSAFE_INLINE')
    if unsafe_inline:
        policy["script-src"] += " 'unsafe-inline'"
        policy["style-src"] += " 'unsafe-inline'"
    elif 'csp_nonce' in g:
        policy["style-src"] += f" 'nonce-{g.csp_nonce}'"
        policy["script-src"] += f" 'nonce-{g.csp_nonce}'"

    safe_srcs = " ".join(set(current_app.config['CSP_SAFE_SRC']))
    return "; ".join(("%s %s" % (k, v.replace("'safe-src'", safe_srcs))).strip() for k, v in policy.items()) + ";"


def csp_nonce():
    if 'csp_nonce' not in g:
        g.csp_nonce = secrets.token_urlsafe(16)[:16]
    return g.csp_nonce
