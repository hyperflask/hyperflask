
class HyperflaskReactive extends HTMLElement {
  connectedCallback() {
    const swap = this.getAttribute('swap');
    const prop = this.getAttribute('prop');
    const escape = this.getAttribute('escape') !== null;
    const url = new URL(this.getAttribute('mercure-url'));
    url.searchParams.append('topic', this.getAttribute('topic'));
    this.eventSource = new EventSource(url);
    const listener = (event) => {
      let data = event.data;
      if (prop) {
        data = JSON.parse(data)[prop];
      }
      if (swap && swap != 'innerHTML') {
        this[escape ? 'insertAdjacentText' : 'insertAdjacentHTML'](swap, data);
      } else {
        this[escape ? 'innerText' : 'innerHTML'] = data;
        window.htmx.process(this);
      }
    };
    const events = this.getAttribute('events');
    if (events) {
      events.split(' ').forEach(event => {
        this.eventSource.addEventListener(event, listener);
      });
    } else {
      this.eventSource.onmessage = listener;
    }
  }

  disconnectedCallback() {
    this.eventSource.close();
  }
}

if (!customElements.get('hf-reactive')) {
  customElements.define('hf-reactive', HyperflaskReactive);
}
