# Medical management system

A clinic management web app built with Flask and MySQL: staff log in, work from a dashboard and
generate prescription PDFs. University project, and the first thing I built where the database
was a real dependency rather than a list in memory.

## What it does

- session based login for clinic staff
- dashboard as the main working screen
- prescription generation, rendered to PDF from a Jinja template
- a `/DBCheck` endpoint that runs `SELECT 1` and reports whether the database connection is
  actually alive

## How it is put together

```
GesMed/
├── app.py           application factory, blueprint registration, error handlers
├── config.py        configuration loaded into app.config
├── controllers/     route handlers, registered as blueprints
├── models/          database access
├── templates/       index, login, dashboard, prescription PDF
└── static/          css and assets
```

It uses the application factory pattern (`create_app()`) instead of a module level `app`, which
is what lets you build the app with different configuration for development and testing without
touching the code.

`flask_mysqldb` talks to MySQL directly with SQL rather than an ORM. That was a deliberate choice
at the time, the course was about SQL and I wanted to write the queries myself.

## Running it

```bash
pip install flask flask-mysqldb mysqlclient
```

Create the database and put the credentials in `config.py`, then:

```bash
cd GesMed
python app.py
```

It listens on <http://localhost:3000>. Check <http://localhost:3000/DBCheck> first, if the
database is not reachable everything else will fail in a much less obvious way.

## What I learned

- The application factory is worth using from the start. Adding it later means untangling every
  import that grabbed the global `app`.
- A health endpoint that actually queries the database, rather than just returning 200, is the
  difference between "the web server is up" and "the app works". I use the same idea in
  everything I have built since.
- Returning JSON from the 404 and 405 handlers keeps the API consistent. An HTML error page in
  the middle of a JSON response is a confusing thing to debug from the client side.
- Generating a PDF from the same Jinja templates as the web pages means one source of truth for
  the layout.

## What I would do differently now

- Credentials belong in environment variables, not in `config.py` in the repository.
- Raw SQL taught me a lot but the queries are scattered through the controllers. SQLAlchemy, or
  at least a data access layer, would keep them in one place.
- No tests. I would not ship anything today without at least covering login and the prescription
  path.
