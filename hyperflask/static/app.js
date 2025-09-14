import htmx from "htmx.org";
import "./app.css";

(function() {
  let triggerElement = false, enableTriggerElement;
  htmx.defineExtension("hf-modal", {
    getSelectors: function() {
        return ['[hf-modal]'];
    },
    onEvent: function(name, evt) {
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

window.htmx = htmx;
export { htmx };

if (window.Alpine) {
    window.Alpine.start()
}
