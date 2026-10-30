import htmx from "htmx.org";

function queryAll(root, selector) {
  const elts = [...root.querySelectorAll(selector)];
  if (root.matches(selector)) {
    elts.unshift(root);
  }
  return elts;
}

htmx.registerExtension("hf-modal", {
  htmx_before_process(root) {
    for (const elt of queryAll(root, "[hf-modal]")) {
      elt.setAttribute("hx-get", elt.getAttribute("hf-modal"));
      elt.setAttribute("hx-target", "body");
      elt.setAttribute("hx-swap", "beforeend");
      if (!elt.hasAttribute("hx-disable")) {
        elt.setAttribute("hx-disable", "this");
      }
    }
  },
  htmx_after_settle(target, detail) {
    const triggerElement = detail.task.sourceElement;
    if (detail.task.type !== "main" || !triggerElement?.hasAttribute("hf-modal")) return;
    for (const dialog of detail.newContent) {
      if (dialog.tagName !== "DIALOG") continue;
      dialog.showModal();
      const form = dialog.querySelector("form[hf-modal-form]");
      if (form) {
        form.setAttribute("hx-target", "closest dialog");
        form.setAttribute("hx-swap", "delete");
        form.setAttribute("hx-disable", "this");
        if (!form.hasAttribute("action")) {
          form.setAttribute("action", triggerElement.getAttribute("hf-modal"));
        }
        setTimeout(() => {
          form.querySelector("input:not([type=hidden])")?.focus();
        }, 100);
      }
    }
  }
});

htmx.registerExtension("hx-bottom-scroll-on-trigger", {
  htmx_after_process(root) {
    for (const elt of queryAll(root, "[hx-bottom-scroll-on-trigger]")) {
      if (elt._hfBottomScroll) continue;
      elt._hfBottomScroll = true;
      elt.scrollTop = elt.scrollHeight - elt.clientHeight;
      elt.classList.add("at-bottom");
      elt.addEventListener("scroll", () => {
        if (elt.scrollTop < elt.scrollHeight - elt.clientHeight - 20) {
          elt.classList.remove("at-bottom");
        } else {
          elt.classList.add("at-bottom");
        }
      });
      elt.addEventListener(elt.getAttribute("hx-bottom-scroll-on-trigger"), () => {
        if (elt.classList.contains("at-bottom")) {
          elt.scrollTop = elt.scrollHeight - elt.clientHeight;
        }
      });
    }
  }
});

// Port of the htmx 1 remove-me extension: removes elements after a delay (eg. remove-me="5s")
htmx.registerExtension("remove-me", {
  htmx_after_process(root) {
    for (const elt of queryAll(root, "[remove-me],[data-remove-me]")) {
      if (elt._hfRemoveMe) continue;
      elt._hfRemoveMe = true;
      const timing = elt.getAttribute("remove-me") || elt.getAttribute("data-remove-me");
      if (timing) {
        setTimeout(() => elt.remove(), htmx.parseInterval(timing));
      }
    }
  }
});

(function () {
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

  htmx.registerExtension("hx-active-url", {
    init() {
      document.addEventListener('DOMContentLoaded', ensureLinksAreActive);
    },
    htmx_before_process(root) {
      for (const elt of queryAll(root, "[hx-href]")) {
        elt.setAttribute('href', elt.getAttribute('hx-href'));
        elt.setAttribute('hx-push-url', elt.getAttribute('hx-href'));
      }
    },
    htmx_after_history_push: ensureLinksAreActive,
    htmx_after_history_replace: ensureLinksAreActive
  });
})();

(function () {
  // Swaps named SSE events into elements, like the htmx 2 sse-swap attribute.
  // The htmx 4 sse extension only swaps unnamed messages into the connection element
  // and dispatches named events as DOM events.
  const SSE_CONNECT_SELECTOR = "[hx-sse\\:connect],[data-hx-sse\\:connect]";
  const SSE_SWAP_ATTR = "hx-sse:swap";
  let api;

  htmx.registerExtension("hx-sse-swap", {
    init(internalAPI) {
      api = internalAPI;
    },
    htmx_sse_before_message(elt, detail) {
      const swapElts = queryAll(elt, "[hx-sse\\:swap]").filter((e) => e.closest(SSE_CONNECT_SELECTOR) === elt);
      if (!swapElts.length) return;
      // unnamed messages are treated as "message" events so that the sse extension does not swap them
      const event = detail.message.event ||= "message";
      for (const swapElt of swapElts) {
        if (!swapElt.getAttribute(SSE_SWAP_ATTR).split(/\s*,\s*/).includes(event)) continue;
        const ctx = api.createRequestContext(swapElt, new CustomEvent(event));
        ctx.text = detail.message.data;
        ctx.swap += " swapEmpty:false";
        detail.waitUntil(htmx.swap(ctx).catch((error) => api.triggerHtmxEvent(swapElt, "htmx:error", { error })));
      }
    }
  });
})();

(function () {
  async function streamInto(ctx, stream) {
    const reader = stream.getReader();
    const decoder = new TextDecoder();
    let text = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done || ctx.hfStreamDone) break;
      text += decoder.decode(value, { stream: true });
      ctx.target.innerHTML = text;
    }
    reader.cancel();
  }

  // Progressively renders suspense responses (streamed with the x-suspense header)
  // while htmx waits for the full response to perform the actual swap
  htmx.registerExtension("hx-stream", {
    htmx_before_request(elt, detail) {
      const ctx = detail.ctx;
      const fetch = ctx.fetch;
      ctx.fetch = async (url, init) => {
        const response = await fetch(url, init);
        if (response.headers.get("x-suspense") !== "1" || !response.body || !(ctx.target instanceof Element)) {
          return response;
        }
        const [body, stream] = response.body.tee();
        streamInto(ctx, stream);
        const teed = new Response(body, { status: response.status, statusText: response.statusText, headers: response.headers });
        Object.defineProperty(teed, "url", { value: response.url });
        return teed;
      };
    },
    htmx_before_swap(elt, detail) {
      detail.ctx.hfStreamDone = true;
    }
  });
})();
