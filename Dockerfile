# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.11
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /eDAVE

# Update image
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y curl unzip

# Copy the source code into the container.
COPY . .

# Download dependencies.
RUN python -m pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

# prepare local data repository
WORKDIR data-processing-pipeline
RUN curl https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_Ubuntu_x64.zip --output gdc.zip
RUN unzip -o gdc.zip
RUN poetry run python run.py

# Create a non-privileged user that the app will run under.
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser
RUN chown -R appuser ../

# Switch to the non-privileged user to run the application.
USER appuser

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
WORKDIR ../app
CMD python -m gunicorn -b 0.0.0.0:8000 app:server
