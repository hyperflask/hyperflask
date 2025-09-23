import htmx from "htmx.org";
import "htmx-ext-sse";
import "./htmx-exts";
import "./app.css";

const DEFAULT_HTMX_EXTS = ['hf-modal', 'hx-bottom-scroll-on-trigger', 'hx-active-url', 'hx-stream'];
document.body.setAttribute('hx-ext', [document.body.getAttribute('hx-ext'), ...DEFAULT_HTMX_EXTS].filter(Boolean).join(","))

window.htmx = htmx;
export { htmx };

if (window.Alpine) {
    window.Alpine.start()
}
