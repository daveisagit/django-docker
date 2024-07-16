# Django + Postgres Template

Setting up a development environment on Windows

- django
- postgres
- nginx
- celery
- rabbitmq

There's a fair bit to do! Not something I do often either once a project has started.

So this repository serves as template for the results from following these steps.

## Highlights

- Based on docker image `python:3.12-slim`
- Postgres is run natively on the machine (not a container) and so persistent
- Compose files for attaching a debugger for both webapp and celery
- Local file system is shared for code, static and media
- Structured logging
- Requirements are assembled via pip-tools for dependency and hashing
- Uses `.env` for environment variables (see end for a sample)

## Install a Postgres server

- Install Postgres
- Django notes on using
  [postgres](https://docs.djangoproject.com/en/5.0/ref/databases/#postgresql-notes)

Versions at time of writing (Postgres v16, Python 3.12.3)

## Prepare a Postgres Database

### Create Database and App User

Most of this you can do this via pgAdmin UI if you prefer

Or, using these commands from within the `\bin` directory of the postgres
install (e.g. `C:\Program Files\PostgreSQL\16\bin`) You will prompted for the
postgres password each time (you may need to tweak the port?)

`createdb -U postgres -p 5432 app-db`

`createuser -U postgres -p 5432 app-user`

Now we need to tweak the DB and User for Django, access the SQL command line via
`psql -U postgres -p 5432`

Prompt
`postgres=#`

Run the following as per the django postgres
[notes](https://docs.djangoproject.com/en/5.0/ref/databases/#postgresql-notes)

Don't forget to choose a more secure password :-)

```sql
ALTER ROLE "app-user" SET client_encoding TO "utf8";
ALTER ROLE "app-user" SET default_transaction_isolation TO "read committed";
ALTER ROLE "app-user" SET timezone TO "UTC";
GRANT ALL PRIVILEGES ON DATABASE "app-db" TO "app-user";
ALTER USER "app-user" SUPERUSER;
ALTER USER "app-user" WITH PASSWORD 'app-user';
```

Then `quit`

## Create the Codebase

The root project folder may well end up containing all sorts of non Django
files, like Docker, github etc.

- Create root project folder (this will be the parent of the Django project)
- Open root in terminal `code .`
- Create venv
- Create a Terminal in VS to run the following
- Install **pip-tools** `python -m pip install pip-tools`
- Create file `requirements.in` and add entries for django and psycopg (for
  postgres) - *limit the version as desired*
- Run pip-compile (see below) to create the actual `requirements.txt`

```shell
pip install pip-tools --upgrade
pip-compile --generate-hashes --allow-unsafe --resolver=backtracking --upgrade 
```

- Run `pip install -r requirements.txt` to add the packages to the venv
- Create the django project `django-admin startproject django_postgres`
- Navigate to root of `manage.py`
- Create the app `python manage.py startapp my_app`
- Renamed `django_postgres` parent folder to `src`
    *(less confusing, the django project still resides in it)*

> Note for windows 10, I needed to also include `psycopg2` as well as `psycopg`

## Better Settings

Update the `settings.py` file to

- Point Django to our new postgres DB
- Use environment variables from `.env` instead of literals in the settings

## Environment Variables

Sample content for the `.env` *file located in your project root*

```text
DJANGO_SECRET_KEY=shh,don't..
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=app-db
SQL_USER=app-user
SQL_PASSWORD=app-user
SQL_HOST=localhost
SQL_PORT=5432
```

## Migrate

Now we are pointing to the right DB we can run migrations. You may need to
restart your venv to ensure the `.env` values are used.

`python manage.py migrate`

Use pgAdmin to confirm the django tables have been created in postgres and not
SQLite by default

## VS Code

- Create a launch configuration in VS Code for a Python Debugger + Django
- Update settings to tell VS Code the root of our source, so intellisense
  imports work

```json
"terminal.integrated.env.windows": {
    "PYTHONPATH": "${workspaceFolder}/src"
}
```

## Run in Docker (if you like)

Add the ability to run/debug in Docker by using VS Docker extension to Add
Docker files and tweak them

You can have VS Code debug in Docker in 2 ways

- Docker: Python - Django
- Python Debugger: Remote Attach

The first does not use the compose files and will launch a new docker container
meaning you don't get to pass in environment variables.

The second requires starting the containers using docker compose up (via right
click on the compose file) and you then use Remote Attach to connect the
debugger.

The following sets up both options, you'll need to add a new configuration for
the second one

### `Dockerfile`

- Replace . with /src on COPY (So looks like COPY /src /app in `Dockerfile`)
- Add os packages to meet pip install needs (e.g. psycopg `RUN apt-get update &&
  apt-get install -y libpq-dev gcc`)
- Add `gunicorn` to `requirements.in` and pip-compile/install (needed for the
  default `docker compose up`)

### Compose Files

- Have the debug file extend the default compose
- / for \ in compose file paths
- Remove src from call to manage.py in `docker-compose.debug.yml`
- Add `env_file` references to `.env` & `.docker.env` in `docker-compose`
- Create `.docker.env` for environment variable overrides such as
  `SQL_HOST=host.docker.internal`

## Add a Superuser

Nav to src where the manage.py file is and run
`python manage.py createsuperuser`
Step up secure as you like on your local machine
[Web App](http://localhost:8000/admin) looks bad, so its time to collectstatic

## Static Files

For local development I like to put create a *"local file system"* called `lfs`
which is made available to the docker container to. The static and media folders
are placed in there.

There may well be other local file system requirements down the road such as
`/logs` or `/temp`.

It is useful to share the lot as subfolders with respect to a local docker
container such that we only need 1 entry in the volumes section of the compose
file. `./src/lfs:/app/lfs`

Tweak `settings.py`

- Add the `lfs/` prefix on `STATIC_URL`
- Add `STATIC_ROOT = os.getenv("DJANGO_STATIC_ROOT", STATIC_URL)`

so now we can override `STATIC_ROOT` from environment variables (i.e. when we
deploy)

- Now we can run `python manage.py collectstatic` from within `/src`
- Add `lfs/` to the `.gitignore` file

## Container Load Balancing (nginx)

To save bothering our app with requests for static and media we can have nginx
serve the content and redirect all other requests to our app

We now call the localhost on port **8080** and compose will forward requests to
**80** where nginx is listening.

It's configured via `nginx.conf` to handle the static and media requests mapped
to /app/lfs/...

- New folder nginx with the dockerfile and configuration

Changes to `docker-compose.yml`

- Rename the existing service to webapp
- Add the nginx service, mapping 8080 to 80

Changes to  `docker-compose.debug.yml`

- Rename the existing service to webapp
- Add the inherited nginx service from above

Changes to `settings.py`

- The `STATIC_URL` is the prefix added by django to all the static URLs
  generated on a page, so this should remain as `static/`

Also, removed `launch.json` entry for starting Docker (as opposed to the Attach
method, no longer needed)

## Trusted Origins

In order for POST requests to work such as /admin/login

- Add `CSRF_TRUSTED_ORIGINS = ensure_array(os.environ.get("CSRF_TRUSTED_ORIGINS", []))` to `settings.py`
- Add entry in `.env` for `CSRF_TRUSTED_ORIGINS=http://localhost:8080`

## Celery + Rabbit Backend

We are going leave `django-postgres-template` as is now and continue in a new
folder `django-postgres-celery-template`. So should we not require backend tasks
from code template, it will save having to remove references to celery + rabbit.

*Should we create a separate database (and user)?*

We are not going add models ourselves but there will be new models for results
and periodic tasks. If this breaks the original `django-postgres-template` then
we could have separate databases but keep a common user `app-user`.

### New Packages

- `django-celery-beat` for periodic tasks (cron etc.)
- `django-celery-results` for persisting the results in the database

We will have container services for `rabbitmq`, `celery-worker` and
`celery-beat` (may add flower too?)

- We will rename the image tag in VS `tasks.json` to
  `django-postgres-celery-template:latest`
- We can debug both the webapp and the celery worker using the same VS task,
  just use the appropriate compose file
- Run `python manage.py migrate` for the beat and results models

## Structured Logging

- Create a `/logs` folder in the local files storage
- Add `django-structlog` to requirements.
- Changes to `settings.py` as per docs
- Changes to `celery.py` as per docs

Can re-use `LOGGING` dict and `structlog.configure` only need be called called
once in `settings.py` and not again `celery.py`

## Reloading Upon Change

For webapp use --reload to automatically pick up code changes and reload the
container (template code to be done later). Use a volume mapping over the whole
source so changes overlay over the image.

## Typical .env

```text
#
# Django
#
DJANGO_SECRET_KEY="............"
DJANGO_LOG_LEVEL=INFO
CSRF_TRUSTED_ORIGINS=http://localhost:8080

#
# Local Postgres database
#

SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=app-db
SQL_USER=app-user
SQL_PASSWORD=....
SQL_HOST=localhost
SQL_PORT=5432

#
# Celery
#
CELERY_BROKER_URL=amqp://rabbitmq:5672
```
