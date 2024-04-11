

export function _(text, ...args) {
  return formatTranslationString(getCatalogValue(text)[1] || text, ...args)
}

export function _p(context, text, ...args) {
  return formatTranslationString(getCatalogValue(text, context)[1] || text, ...args)
}

export function _n(singular, plural, count, args, context) {
  args = args || {};
  args['count'] = count;
  const value = getCatalogValue(singular, context);
  if (value) {
    if (value[1]) {
      singular = value[1];
    }
    if (value[2]) {
      plural = value[2];
    }
  }
  if (count > 1) {
    return formatTranslationString(plural, args);
  }
  return formatTranslationString(singular, args);
}

export function _np(context, singular, plural, count, args) {
  return _n(singular, plural, count, args, context);
}

function formatTranslationString(text, ...data) {
  if (data.length) {
    if (data.length === 1 && $.isPlainObject(data[0])) {
      data = data[0];
    }
    for (let [key, value] of Object.entries(data)) {
      text = text.replace(new RegExp('\\{' + key + '\\}', 'gi'), value);
    }
  }
  return text;
}

function getCatalogValue(text, context) {
  const messageId = context ? context + '::' + text : text;
  if (typeof(catalog[messageId]) !== 'undefined' && catalog[messageId][1]) {
    return catalog[messageId];
  }
  return [null, null];
}

export function getCurrentLocale() {
  
}