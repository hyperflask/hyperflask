<div><img src="https://raw.githubusercontent.com/hyperflask/hyperflask/main/assets/banner.svg" width="100%"></div>
<hr>
<div align="center">

**Full stack Python web framework to build websites and web apps with as little boilerplate as possible**

**⚠️ This is a work in progress project which is not functionnal yet ⚠️**

![Project Status](https://img.shields.io/badge/status-prototype-red) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/hyperflask/hyperflask/python.yml?branch=main)

[hyperflask.dev](https://hyperflask.dev) • [Get started](https://hyperflask.dev/getting-started) • [Docs](https://hyperflask.dev/guides) • [Example apps](https://github.com/hyperflask/examples)

</div>

A [Flask](https://flask.palletsprojects.com)-based (very) opiniated Python web framework where all the tech choices have been made. Hyperflask combines multiple Flask extensions and frontend libraries into a seamless experience.

**This project is part of the [Hyperflask Stack](https://hyperflask.dev).**

Features and technologies:

 - Web framework built on top of [Flask](https://flask.palletsprojects.com) as a set of extensions
 - File-based and/or app-based routing
 - A new file format combining python code in frontmatter and html templates to define routes
 - SQL focused ORM with [sqlorm](https://github.com/hyperflask/sqlorm), optimized for [sqlite](https://www.sqlite.org/)
 - Modern asset pipeline using [esbuild](https://esbuild.github.io/) and [tailwindcss](https://tailwindcss.com/)
 - Deep integration with [htmx](https://htmx.org/)
 - Easily create reusable backend and frontend components, compatible with [Storybook](https://storybook.js.org)f
 - Build frontend components using Web Components, [Alpine.js](https://alpinejs.dev/), [Stimulus](https://stimulus.hotwired.dev/) and more. Mix technologies at will.
 - Component library based on [daisyUI](https://daisyui.com/) with icons from [Bootstrap Icons](https://icons.getbootstrap.com/)
 - Seamless reactivity between frontend and backend
 - Authentication and user management with social logins and MFA
 - Static content collections to easily create blogs and manage static content
 - File management with built-in image manipulation and S3 integration
 - Template based emails with [mjml](https://mjml.io) support
 - Background tasks using [dramatiq](https://dramatiq.io/)
 - Push support for realtime pages using [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
 - I18n using [gettext](https://www.gnu.org/software/gettext/)
 - Easily create REST APIs and automatically generate documentation
 - Static, hybrid or dynamic modes for content serving
 - Observable with [OpenTelemetry](https://opentelemetry.io/)

[Hyperflask-Start](https://github.com/hyperflask/hyperflask-start) should be used to create new projects:

 - Dev environment based on [Development Containers](https://containers.dev/)
 - Optimized for VScode with breakpoint debugging for frontend and backend
 - [Mailpit](https://github.com/axllent/mailpit) for email testing
 - Deployments using [Hyperflask-Deploy](https://github.com/hyperflask/hyperflask-deploy)

## Project status

**Hyperflask is being actively developed and is not yet ready to be used.**

Checkout the list of all the projects developed as part of the Hyperflask Stack and their current development status on the [Hyperflask Github organization homepage](https://github.com/hyperflask).

Status overview:

| Feature | Status |
| --- | --- |
| Core experience (start project, dev, deploy) | 🚧 |
| File based routing with mix code page format | ✅ |
| ORM | ✅ |
| Assets pipeline | ✅ |
| Component system + component library | 🚧 (component system almost done, need to create macros for daisyui) |
| SSE push | ✅ |
| Collections | 🚧 (finalizing) |
| Upload files | 🚧 (missing S3 improvements) |
| Emails | 🚧 |
| User management and auth | 🚧 |
| Static site generation | ❌ |
| I18n | 🚧 (finalizing) |
| PWA | ❌ |
| Runner | ✅ |

## Flask extensions

Hyperflask itself is minimal and mostly a collection of Flask extensions seamlessly integrated together.

A good part of these extensions is developed as part of the Hyperflask project. Checkout the [Hyperflask organization page](https://github.com/hyperflask) for a list of all these projects.

| Name | Description |
| --- | --- |
| [Flask-Apispec-Hyper](https://github.com/hyperflask/flask-apispec-hyper) | [Flask-Apispec](https://github.com/jmcarp/flask-apispec) fork with updates and fixes
| [Flask-Assets-Pipeline](https://github.com/hyperflask/flask-assets-pipeline) | Modern asset pipeline using [esbuild](https://esbuild.github.io/)
| [Flask-Babel-Hyper](https://github.com/hyperflask/flask-babel-hyper) | [Flask-Babel](https://github.com/python-babel/flask-babel) fork with additional utilities
| [Flask-Collections](https://github.com/hyperflask/flask-collections) | Manage collections of static content
| [Flask-Configurator](https://github.com/hyperflask/flask-configurator) | File based configuration
| [Flask-DebugToolbar](https://github.com/pallets-eco/flask-debugtoolbar) | Debug Toolbar
| [Flask-Dramatiq](https://flask-dramatiq.readthedocs.io) | Background tasks powered by [Dramatiq](https://dramatiq.io/) |
| [Flask-File-Routes](https://github.com/hyperflask/flask-file-routes) | File-based routing with a new file format combining python and jinja template in a single file
| [Flask-Files](https://github.com/hyperflask/flask-files) | [Fsspec](https://filesystem-spec.readthedocs.io/en/latest/) based files management (upload, storage and image manipulation)
| [Frozen-Flask](https://github.com/Frozen-Flask/Frozen) | Generate a static website from your Flask app |
| [Flask-Geo](https://github.com/hyperflask/flask-geo) | Geolocation using [Maxmind](https://www.maxmind.com/en/geoip-databases)
| [Htmx-Flask](https://github.com/sponsfreixes/htmx-flask) | HTMX integration for Flask |
| [Flask-Login](https://github.com/maxcountryman/flask-login) | User session management |
| [Flask-Mailman](https://github.com/waynerv/flask-mailman) | Send emails |
| [Flask-Mailman-Templates](https://github.com/hyperflask/flask-mailman-templates) | Email templates for [Flask-Mailman](https://github.com/waynerv/flask-mailman)
| [Flask-Mercure-SSE](https://github.com/hyperflask/flask-mercure-sse) | Push events via server-sent events using the [Mercure](https://mercure.rocks) protocol
| [Flask-Observability](https://github.com/hyperflask/flask-observability) | Observable Flask apps with [OpenTelemetry](https://opentelemetry.io/), logging and more
| [Flask-SQLORM](https://github.com/hyperflask/flask-sqlorm) | Flask integration of [sqlorm](https://github.com/hyperflask/sqlorm)
| [Flask-Super-Macros](https://github.com/hyperflask/flask-super-macros) | Better macro management for Jinja
| [Flask-Talisman](https://github.com/wntrblm/flask-talisman) | HTTP security headers for Flask
| [Flask-WTF](https://flask-wtf.readthedocs.io) | [WTForms](https://wtforms.readthedocs.io) integration

## Using without Hyperflask-Start

1. Create your project directory: `mkdir example-project && cd example-project`
2. Create and activate a virtualenv: `python -m venv .venv && source .venv/bin/activate`
3. `pip install hyperflask`
4. Create a pages directory: `mkdir pages`
5. Create your index page: `echo "hello world" > pages/index.html`
6. Start a development server using `hyperflask dev`
