FROM python:3.10-slim

# update image
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y curl unzip
RUN pip install poetry

# prepare app
WORKDIR eDAVE
COPY . .
RUN poetry install

# prepare local data repository
WORKDIR data-processing-pipeline
RUN curl https://gdc.cancer.gov/files/public/file/gdc-client_v1.6.1_Ubuntu_x64.zip --output gdc.zip
RUN unzip -o gdc.zip
RUN poetry run python run.py

# start app
WORKDIR ../app
CMD ["poetry", "run", "gunicorn", "-b 0.0.0.0:8000", "app:server"]
