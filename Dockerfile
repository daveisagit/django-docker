# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# May need to add extra packages on top of slim
# i.e. postgres needs the psycopg python package which in turn needs the gcc compiler
RUN apt-get update \
    && apt-get install -y libpq-dev gcc

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY /src /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# This will be used the default docker-compose which has no command / entry point
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "django_postgres.wsgi", "--reload"]
