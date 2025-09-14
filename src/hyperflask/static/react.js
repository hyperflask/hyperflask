import * as React from 'react';
import { createRoot } from 'react-dom/client';

class HyperflaskReactComponent extends HTMLElement {
  connectedCallback() {
    import(this.getAttribute("component-url")).then(module => {
      const props = JSON.parse(this.getAttribute('props'));
      createRoot(this).render(React.createElement(module.default, props));
    });
  }
}

if (!customElements.get('hf-react-component')) {
  customElements.define('hf-react-component', HyperflaskReactComponent);
}
