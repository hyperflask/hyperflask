from flask import current_app, json
from flask_configurator.config import deep_update_dict
from jinja_super_macros import html_tag
from markupsafe import Markup
import inspect


DEFAULT_METADATA = {
    "charset": "utf-8",
    "viewport": "width=device-width, initial-scale=1.0",
}

LINK_METADATA = ["icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed",
                 "manifest", "canonical", "alternate", "archives", "assets", "bookmarks"]


def metadata_tags(metadata=None, title_template=None, **kwargs):
    _metadata = dict(DEFAULT_METADATA)
    _metadata.update(current_app.config.get('SITE_METADATA', {}))
    deep_update_dict(_metadata, metadata or {})
    deep_update_dict(_metadata, kwargs)
    tags = []

    if title_template is None:
        title_template = current_app.config.get('SITE_TITLE', None)
    title = generate_title(_metadata.pop("title", None), title_template)
    if title:
        tags.append(f"<title>{title}</title>")

    for name, value in _metadata.items():
        if name.startswith("_"):
            continue
        if name in METADATA_GENERATORS:
            rv = METADATA_GENERATORS[name](name, value, _metadata)
        else:
            rv = metadata_tag(name, value, _metadata)
        if inspect.isgenerator(rv) or isinstance(rv, (list, tuple)):
            tags.extend(list(rv))
        else:
            tags.append(rv)

    return Markup("\n".join(tags))


def generate_title(title, title_template=None):
    if isinstance(title, dict) and "absolute" in title:
        return title["absolute"]
    if title_template:
        if isinstance(title_template, str):
            title_template = {"template": title_template}
        if "default" in title_template and title is None:
            return title_template["default"]
        return title_template["template"].replace("%s", title or "")
    return title


def metadata_tag(name, value, metadata, force_link=False, is_url=None, key_separator=":"):
    if not isinstance(value, (list, tuple)):
        value = [value]
    is_link = force_link is True or name in LINK_METADATA
    if is_link and is_url is None:
        is_url = True
    for v in value:
        if isinstance(v, dict):
            for sub_name, sub_value in v.items():
                sub_force_link = sub_name in force_link if isinstance(force_link, (list, tuple)) else force_link
                sub_is_url = sub_name in is_url if isinstance(is_url, (list, tuple)) else is_url
                yield from metadata_tag(f"{name}{key_separator}{sub_name}", sub_value, metadata,
                                        force_link=sub_force_link, is_url=sub_is_url, key_separator=key_separator)
            continue
        if is_url:
            v = _metadata_url(v, metadata)
        if is_link:
            yield html_tag("link", rel=name, href=v)
        else:
            yield html_tag("meta", name=name, content=v)


def metadata_keywords(name, value, metadata):
    if isinstance(value, (list, tuple)):
        value = ",".join(value)
    return html_tag("meta", name="keywords", content=value)


def metadata_author(name, value, metadata):
    if isinstance(value, (list, tuple)):
        yield from (metadata_author(name, v, metadata) for v in value)
        return
    url = None
    if isinstance(value, dict):
        value = value.get("name")
        url = value.get("url")
    if url:
        yield html_tag("link", rel="author", href=_metadata_url(url, metadata))
    if value:
        yield html_tag("meta", name="author", content=value)


def metadata_alternates(name, value, metadata):
    alt_attr = {"alternate-lang": "hreflang", "alternate-media": "media", "alternate-type": "type"}.get(name, "hreflang")
    for alt, href in value.items():
        yield html_tag("link", rel="alternate", href=_metadata_url(href, metadata), **{alt_attr: alt})


def metadata_robots(name, robots, metadata):
    if not isinstance(robots, dict):
        return html_tag("meta", name=name, content=robots)
    content = []
    for directive, value in robots.items():
        if isinstance(value, bool):
            if value:
                content.append(directive)
        else:
            content.append(f"{directive}:{value}")
    return html_tag("meta", name=name, content=", ".join(content))


def metadata_opengraph(name, value, metadata):
    for key, value in value.items():
        if key in ("image", "video") and isinstance(value, dict):
            yield from metadata_tag(f"og:{key}", value["url"], metadata, is_url=True)
            if "width" in value:
                yield from metadata_tag(f"og:{key}:width", value["width"], metadata)
            if "height" in value:
                yield from metadata_tag(f"og:{key}:height", value["height"], metadata)
            if "alt" in value:
                yield from metadata_tag(f"og:{key}:alt", value["alt"], metadata)
        elif key == "images" or key == "image" and isinstance(value, (list, tuple)):
            yield from (metadata_opengraph(None, {"image": v}, metadata) for v in value)
        elif key == "videos" or key == "video" and isinstance(value, (list, tuple)):
            yield from (metadata_opengraph(None, {"video": v}, metadata) for v in value)
        else:
            yield from metadata_tag(f"og:{key}", value, metadata, is_url=key in ("url", "audio"))


def metadata_twitter(name, value, metadata):
    yield from metadata_tag(name, value, metadata, is_url=("image", "url", "card"))


def metadata_json_ld(name, value, metadata):
    if isinstance(value, (list, tuple)):
        yield from (metadata_json_ld(name, v, metadata) for v in value)
        return
    if isinstance(value, dict):
        value = json.dumps(value, indent=2)
    return f"<script type=\"application/ld+json\">\n{value}\n</script>"


def metadata_apple(name, value, metadata):
    force_link = (
        "touch-icon",
        "touch-icon-precomposed",
        "touch-startup-image"
    )
    yield from metadata_tag("apple-", value, metadata, force_link=force_link, key_separator="-")


def metadata_applinks(name, value, metadata):
    yield from metadata_tag("al:", value, metadata)


def _metadata_url(url, metadata):
    if metadata.get("_baseurl") and not url.startswith("http"):
        return (metadata["_baseurl"] + url).rstrip("/")
    return url


METADATA_GENERATORS = {
    "keywords": metadata_keywords,
    "author": metadata_author,
    "alternate-lang": metadata_alternates,
    "alternate-media": metadata_alternates,
    "alternate-type": metadata_alternates,
    "robots": metadata_robots,
    "googlebot": metadata_robots,
    "og": metadata_opengraph,
    "opengraph": metadata_opengraph,
    "twitter": metadata_twitter,
    "apple": metadata_apple,
    "applinks": metadata_applinks,
    "json-ld": metadata_json_ld
}
