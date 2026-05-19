# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start the dev server (port 5001)
./run.sh
# or directly:
venv/bin/python3 app.py

# Kill the server if port 5001 is already in use
lsof -ti :5001 | xargs kill -9

# Run all tests
venv/bin/pytest

# Run a single test file
venv/bin/pytest tests/test_routes.py

# Run a single test by name
venv/bin/pytest tests/test_routes.py::TestLanding::test_landing_returns_200

# Run tests with coverage
venv/bin/coverage run -m pytest && venv/bin/coverage report
```

## Architecture

**ASKFLEETS** is a customer-facing fleet delivery booking website built with Flask. It is a thin server-side rendering app with no database yet — session state is stored in Flask's signed cookie session.

### Request flow

```
Browser → Flask (app.py) → render_template → templates/*.html
                                            → static/css/*.css
```

### Key files

- `app.py` — all routes. The `dashboard_required` decorator enforces session-based auth; only `admin` and `manager` roles (stored in `session["role"]`) can access `/dashboard`.
- `templates/landing.html` — the main public page. Contains all its own CSS inline in a `<style>` block (design tokens, layout, animations). Shared/section-specific CSS is split to `static/css/landing.css`.
- `static/css/landing.css` — CSS for the Delivery Partners scroll strip and FAQ accordion (appended separately from the inline styles in the template).
- `templates/features.html` / `static/css/features.css` — Features page.
- `templates/dashboard.html` / `static/css/dashboard.css` — Protected internal dashboard (admin/manager only).
- `templates/unauthorized.html` — Rendered with 403 when a logged-in user lacks the required role.

### CSS split convention

`landing.html` keeps core layout CSS inline (`<style>` in `<head>`). CSS for self-contained sections added later (partners strip, FAQ) lives in `landing.css`. Keep this pattern when adding new sections.

### Auth

Session keys used by the auth decorator:
- `session["user"]` — present when logged in
- `session["role"]` — must be `"admin"` or `"manager"` to access `/dashboard`

There is no login route in `app.py` yet — `TestLogin` tests in `tests/test_routes.py` are stale and will fail. Do not add a `/login` route without also updating those tests.

### Environment

`.env` is git-ignored. It holds Twilio credentials (currently unused) and `FLASK_SECRET_KEY`. Copy structure from `.env` comments when setting up a new environment.

## MCP Tools: code-review-graph

Use graph tools before Grep/Glob/Read for codebase exploration.

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes |
| `get_impact_radius` | Understanding blast radius of a change |
| `query_graph` | Tracing callers, callees, imports, tests |
| `semantic_search_nodes` | Finding functions/classes by name |
