import htmx from "htmx.org";
import "htmx.org/dist/ext/hx-sse.js";
import "./htmx-exts";
import "./app.css";

window.htmx = htmx;
export { htmx };

if (window.Alpine) {
    window.Alpine.start()
}
