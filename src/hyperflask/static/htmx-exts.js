import htmx from "htmx.org";

(function () {
  let triggerElement = false, enableTriggerElement;
  htmx.defineExtension("hf-modal", {
    getSelectors() {
      return ['[hf-modal]'];
    },
    onEvent(name, evt) {
      if (name === "htmx:beforeProcessNode" && evt.target.hasAttribute("hf-modal")) {
        evt.target.setAttribute("hx-get", evt.target.getAttribute("hf-modal"));
        evt.target.setAttribute("hx-target", "body");
        evt.target.setAttribute("hx-swap", "beforeend");
      } else if (name === "htmx:beforeRequest" && evt.target.hasAttribute("hf-modal")) {
        triggerElement = evt.target;
        enableTriggerElement = !evt.target.disabled;
        evt.target.disabled = true;
      } else if (name === "htmx:load" && triggerElement) {
        if (evt.target.tagName === "DIALOG") {
          evt.target.showModal();
          const form = evt.target.querySelector("form[hf-modal-form]");
          if (form) {
            form.setAttribute("hx-target", "closest dialog");
            form.setAttribute("hx-swap", "delete");
            form.setAttribute("hx-disabled-elt", "this");
            if (!form.hasAttribute("action")) {
              form.setAttribute("action", triggerElement.getAttribute("hf-modal"));
            }
            setTimeout(() => {
              form.querySelector("input:not([type=hidden])")?.focus();
            }, 100);
          }
        }
        if (enableTriggerElement) {
          triggerElement.disabled = false;
        }
        triggerElement = null;
      }
    }
  });
})();

htmx.defineExtension("hx-bottom-scroll-on-trigger", {
  getSelectors() {
    return ['[hx-bottom-scroll-on-trigger]'];
  },
  onEvent(name, evt) {
    if (name === "htmx:afterProcessNode" && evt.target.hasAttribute("hx-bottom-scroll-on-trigger")) {
      const elt = evt.target;
      elt.scrollTop = elt.scrollHeight - elt.clientHeight;
      elt.classList.add("at-bottom");
      elt.addEventListener("scroll", (e) => {
        if (e.target.scrollTop < e.target.scrollHeight - e.target.clientHeight - 20) {
          e.target.classList.remove("at-bottom");
        } else {
          e.target.classList.add("at-bottom");
        }
      });
      return;
    }

    const eventName = evt.target.getAttribute("hx-bottom-scroll-on-trigger");
    if (name === eventName && evt.target.classList.contains("at-bottom")) {
      evt.target.scrollTop = evt.target.scrollHeight - evt.target.clientHeight;
    }
  }
});

htmx.defineExtension("hx-active-url", {
  init() {
    function ensureLinksAreActive() {
      const nodes = document.querySelectorAll('a[hx-active-url], [hx-active-url] a');
      nodes.forEach((a) => {
        let url;
        for (const attr of ['hx-push-url', 'hx-replace-url', 'href', 'hx-get']) {
          if (a.hasAttribute(attr)) {
            if (attr !== "href" && a.getAttribute(attr) === "true") {
              url = new URL(a.getAttribute('hx-get'), window.location.origin);
            } else {
              url = new URL(a.getAttribute(attr), window.location.origin);
            }
            break;
          }
        }
        if (!url) return;
        const activeClass = a.closest("[hx-active-url]")?.getAttribute("hx-active-url");
        if (!activeClass) return;
        if (url.pathname === window.location.pathname && url.search === window.location.search) {
          a.classList.add(activeClass);
        } else {
          a.classList.remove(activeClass);
        }
      });
    }
    document.addEventListener('DOMContentLoaded', ensureLinksAreActive);
    document.addEventListener("htmx:pushedIntoHistory", ensureLinksAreActive);
  },
  getSelectors() {
    return ['[hx-href]'];
  },
  onEvent(name, evt) {
    if (name === "htmx:beforeProcessNode" && evt.target.hasAttribute("hx-href")) {
      evt.target.setAttribute('href', evt.target.getAttribute('hx-href'));
      evt.target.setAttribute('hx-push-url', evt.target.getAttribute('hx-href'));
    }
  }
});

htmx.defineExtension("hx-stream", {
  onEvent: function (name, evt) {
    if (name === "htmx:beforeRequest") {
      const target = evt.detail.target;
      const xhr = evt.detail.xhr;
      let stream = false;
      xhr.addEventListener('readystatechange', function () {
        if (xhr.readyState == xhr.HEADERS_RECEIVED && xhr.getResponseHeader('x-suspense') === '1') {
          stream = true;
          target.innerHTML = xhr.responseText;
        } else if (xhr.readyState === xhr.LOADING && stream) {
          target.innerHTML = xhr.responseText;
        } else if (xhr.readyState === xhr.DONE) {
          stream = false;
        }
      });
    }
    return true;
  }
});
