from flask import current_app, json
from flask_babel import get_locale
from flask_configurator.config import deep_update_dict
from jinja2.utils import htmlsafe_json_dumps
from jinja_super_macros import html_tag as _html_tag
from markupsafe import Markup, escape
from babel import Locale, UnknownLocaleError
import inspect


DEFAULT_METADATA = {
    "charset": "utf-8",
    "viewport": "width=device-width, initial-scale=1.0",
}

LINK_METADATA = ["icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed",
                 "manifest", "canonical", "alternate", "archives", "assets", "bookmarks"]

PROPERTY_METADATA_PREFIXES = ("og:", "fb:", "al:", "article:", "book:", "profile:")


def html_tag(tagname, **attrs):
    # jinja-super-macros 0.2.0 does not escape attribute values (escaped values are Markup,
    # so they are not escaped twice by versions that do)
    return _html_tag(tagname, **{k: escape(v) for k, v in attrs.items() if v is not None})


def metadata_tags(metadata=None, title_template=None, **kwargs):
    _metadata = dict(DEFAULT_METADATA)
    _metadata.update(current_app.config.get('SITE_METADATA', {}))
    deep_update_dict(_metadata, metadata or {})
    deep_update_dict(_metadata, kwargs)
    tags = []

    # charset must be the first tag of the head, before the title
    charset = _metadata.pop("charset", None)
    if charset:
        tags.append(html_tag("meta", charset=charset))

    if title_template is None:
        title_template = current_app.config.get('SITE_TITLE', None)
    title = generate_title(_metadata.pop("title", None), title_template)
    if title:
        tags.append(f"<title>{escape(title)}</title>")

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


def document_lang():
    """Returns the BCP 47 language tag of the current document"""
    lang = current_app.config.get("SITE_LANG")
    if lang:
        return lang.replace("_", "-")
    locale = get_locale()
    return str(locale).replace("_", "-") if locale else "en"


def document_dir():
    """Returns the text direction (ltr or rtl) of the current document"""
    try:
        return Locale.parse(document_lang(), sep="-").text_direction
    except (ValueError, UnknownLocaleError):
        return "ltr"


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
        elif name.startswith(PROPERTY_METADATA_PREFIXES):
            yield html_tag("meta", property=name, content=v)
        else:
            yield html_tag("meta", name=name, content=v)


def metadata_keywords(name, value, metadata):
    if isinstance(value, (list, tuple)):
        value = ",".join(value)
    return html_tag("meta", name="keywords", content=value)


def metadata_author(name, value, metadata):
    if isinstance(value, (list, tuple)):
        for v in value:
            yield from metadata_author(name, v, metadata)
        return
    url = None
    if isinstance(value, dict):
        url = value.get("url")
        value = value.get("name")
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
    for key, val in value.items():
        if key in ("images", "videos") or key in ("image", "video") and isinstance(val, (list, tuple)):
            for v in val:
                yield from metadata_opengraph(name, {key.rstrip("s"): v}, metadata)
        elif key in ("image", "video") and isinstance(val, dict):
            yield from metadata_tag(f"og:{key}", val["url"], metadata, is_url=True)
            for prop in ("width", "height", "alt"):
                if prop in val:
                    yield from metadata_tag(f"og:{key}:{prop}", val[prop], metadata)
        else:
            yield from metadata_tag(f"og:{key}", val, metadata,
                                    is_url=key in ("url", "audio", "image", "video"))


def metadata_twitter(name, value, metadata):
    yield from metadata_tag(name, value, metadata, is_url=("image", "url"))


def metadata_theme_color(name, value, metadata):
    if not isinstance(value, dict):
        return html_tag("meta", name=name, content=value)
    # keys are color schemes (light, dark) or media queries
    return [html_tag("meta", name=name, content=color,
                     media=f"(prefers-color-scheme: {media})" if media in ("light", "dark") else media)
            for media, color in value.items()]


def metadata_json_ld(name, value, metadata):
    if isinstance(value, (list, tuple)):
        for v in value:
            yield from metadata_json_ld(name, v, metadata)
        return
    if isinstance(value, str):
        # "</" can only appear inside JSON strings where "<\/" is equivalent
        value = value.replace("</", "<\\/")
    else:
        # escapes <, >, & and ' so the content cannot close the script tag
        value = htmlsafe_json_dumps(value, dumps=json.dumps, indent=2)
    yield f"<script type=\"application/ld+json\">\n{value}\n</script>"


def metadata_apple(name, value, metadata):
    force_link = (
        "touch-icon",
        "touch-icon-precomposed",
        "touch-startup-image"
    )
    yield from metadata_tag("apple", value, metadata, force_link=force_link, key_separator="-")


def metadata_applinks(name, value, metadata):
    yield from metadata_tag("al", value, metadata)


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
    "theme-color": metadata_theme_color,
    "json-ld": metadata_json_ld
}
