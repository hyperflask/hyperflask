from flask import current_app
from jinja_super_macros import html_tag
from flask_assets_pipeline import image_attrs


def image_tag(src, priority=False, preload=False, placeholder=True, loading=None, decoding=None, **attrs):
    if not loading:
        loading = current_app.config["IMAGES_DEFAULT_LOADING"]
    if not decoding:
        decoding = current_app.config["IMAGES_DEFAULT_DECODING"]
    if priority:
        preload = True
        attrs.setdefault("fetchpriority", "high")
    if preload:
        current_app.assets.include([(src, {"modifier": "preload", "content_type": "image"})])
        if loading == "lazy":
            loading = "eager"
    _attrs = image_attrs(src)
    if not placeholder and "style" in _attrs:
        del _attrs["style"]
    if loading:
        _attrs["loading"] = loading
    if decoding:
        _attrs["decoding"] = decoding
    _attrs.update(attrs)
    return html_tag("img", **_attrs)
