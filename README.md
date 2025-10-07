<div><img src="https://raw.githubusercontent.com/hyperflask/hyperflask/main/assets/banner.svg" width="100%"></div>
<hr>
<div align="center">

**Full stack Python web framework to build websites and web apps with as little boilerplate as possible**

[hyperflask.dev](https://hyperflask.dev) • [Get started](https://hyperflask.dev/getting-started) • [Docs](https://hyperflask.dev/guides) • [Example apps](https://github.com/hyperflask/examples)

</div>

A [Flask](https://flask.palletsprojects.com)-based (very) opiniated full-stack web framework where all the tech choices have been made. Hyperflask combines multiple Flask extensions and frontend libraries into a seamless experience.

Features and technologies:

 - Web framework built on top of [Flask](https://flask.palletsprojects.com) as a set of extensions
 - File-based and/or app-based routing
 - A new file format combining python code in frontmatter and html templates to define routes
 - SQL focused ORM with [sqlorm](https://github.com/hyperflask/sqlorm), optimized for [sqlite](https://www.sqlite.org/)
 - Modern asset pipeline using [esbuild](https://esbuild.github.io/) and [tailwindcss](https://tailwindcss.com/)
 - Deep integration with [htmx](https://htmx.org/)
 - Easily create reusable backend and frontend components
 - Build frontend components using Web Components, [Alpine.js](https://alpinejs.dev/), [React](https://react.dev) and more. Mix technologies at will.
 - Component library based on [daisyUI](https://daisyui.com/) with icons from [Bootstrap Icons](https://icons.getbootstrap.com/)
 - Authentication and user management with social logins and MFA
 - Static content collections to easily create blogs and manage static content
 - File management with built-in image manipulation and S3 integration
 - Template based emails with [mjml](https://mjml.io) support
 - Background tasks using [dramatiq](https://dramatiq.io/) with sqlite as the default broker
 - Push support for realtime pages using [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
 - I18n using [gettext](https://www.gnu.org/software/gettext/)
 - Static, hybrid or dynamic modes for content serving

[Hyperflask-Start](https://github.com/hyperflask/hyperflask-start) should be used to create new projects:

 - Dev environment based on [Development Containers](https://containers.dev/)
 - Optimized for VScode with breakpoint debugging for frontend and backend
 - [Mailpit](https://github.com/axllent/mailpit) for email testing
 - Deployments using [docker-web-deploy](https://github.com/hyperflask/docker-web-deploy)

## Project status

**Hyperflask is being actively developed and is not yet ready to be used.**

Checkout the list of all the projects developed as part of the Hyperflask stack and their current development status on the [Hyperflask Github organization homepage](https://github.com/hyperflask).

[Project status and roadmap](https://hyperflask.dev/roadmap)

## Flask extensions

Hyperflask itself is minimal and mostly a collection of Flask extensions seamlessly integrated together.

A good part of these extensions is developed as part of the Hyperflask project. Checkout the [Hyperflask organization page](https://github.com/hyperflask) for a list of all these projects.

| Name | Description |
| --- | --- |
| [Flask-Assets-Pipeline](https://github.com/hyperflask/flask-assets-pipeline) | Modern asset pipeline using [esbuild](https://esbuild.github.io/)
| [Flask-Babel-Hyper](https://github.com/hyperflask/flask-babel-hyper) | [Flask-Babel](https://github.com/python-babel/flask-babel) fork with additional utilities
| [Flask-Collections](https://github.com/hyperflask/flask-collections) | Manage collections of static content
| [Flask-Configurator](https://github.com/hyperflask/flask-configurator) | File based configuration
| [Flask-DebugToolbar](https://github.com/pallets-eco/flask-debugtoolbar) | Debug Toolbar
| [Flask-File-Routes](https://github.com/hyperflask/flask-file-routes) | File-based routing with a new file format combining python and jinja template in a single file
| [Flask-Files](https://github.com/hyperflask/flask-files) | [Fsspec](https://filesystem-spec.readthedocs.io/en/latest/) based files management (upload, storage and image manipulation)
| [Frozen-Flask](https://github.com/Frozen-Flask/Frozen) | Generate a static website from your Flask app |
| [Flask-Geo](https://github.com/hyperflask/flask-geo) | Geolocation using [Maxmind](https://www.maxmind.com/en/geoip-databases)
| [Htmx-Flask](https://github.com/sponsfreixes/htmx-flask) | HTMX integration for Flask |
| [Flask-Login](https://github.com/maxcountryman/flask-login) | User session management |
| [Flask-Mailman](https://github.com/waynerv/flask-mailman) | Send emails |
| [Flask-Mailman-Templates](https://github.com/hyperflask/flask-mailman-templates) | Email templates for [Flask-Mailman](https://github.com/waynerv/flask-mailman)
| [Flask-Mercure-SSE](https://github.com/hyperflask/flask-mercure-sse) | Push events via server-sent events using the [Mercure](https://mercure.rocks) protocol
| [Flask-SQLORM](https://github.com/hyperflask/flask-sqlorm) | Flask integration of [sqlorm](https://github.com/hyperflask/sqlorm)
| [Flask-Super-Macros](https://github.com/hyperflask/flask-super-macros) | Better macro management for Jinja
| [Flask-Suspense](https://github.com/hyperflask/flask-suspense) | Suspense for Flask
| [Flask-WTF](https://flask-wtf.readthedocs.io) | [WTForms](https://wtforms.readthedocs.io) integration

## Using without Hyperflask-Start

1. Create your project directory: `mkdir example-project && cd example-project`
2. Create and activate a virtualenv: `python -m venv .venv && source .venv/bin/activate`
3. `pip install hyperflask`
4. Run `hyperflask init .`
5. Start a development server using `hyperflask dev`
