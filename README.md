![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)
![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)

![Ubuntu 22.04](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

### eDAVE - extension for [GDC Data Analysis, Visualization, and Exploration (DAVE) Tools](https://gdc.cancer.gov/analyze-data/gdc-dave-tools)


#### Goal
The goal of this project is to provide a highly efficient GUI to analyse, visualize and explore datasets from **GDC** (Genomic Data Commons).
This project contains two main components:

```
- data-processing-pipeline/ -> implements data processing pipeline to build local data repository.
- app/ -> implements Dash-based app which is an interface to local data repository.
```

#### Contact
jan.binkowski[at]pum.edu.pl

#### App
[Go to the web app](https://edave.pum.edu.pl/)

#### Run eDAVE locally
Because of technical limitations web-based eDAVE is providing access to only part of the data
deposited in the GDC. To overcome this obstacle a user may run eDAVE locally. To do so a user
should follow one out of two alternative paths (described below) as well as open
`data-processing-pipeline/config.json` and update the fields listed below.

    - FILES_LIMIT # max files/samples in local data repository
    - MIN_COMMON_SAMPLES # min common samples (exp and met data) per single category
    - MIN_SAMPLES_PER_SAMPLE_GROUP # min number of samples per single category
    - MAX_SAMPLES_PER_SAMPLE_GROUP # max number of samples per single category


### Path 1: run app in poetry environment (long-path)
#### 1. Prepare environment
1.1 make sure that You have python >= 3.10 installed
1.2 install [poetry](https://python-poetry.org/) dependency manager

       pip install poetry

1.3 clone repository

       git clone https://github.com/ClinicalEpigeneticsLaboratory/eDAVE.git

1.4 open project directory and install required dependencies

       poetry install

1.5 install pre-commit [optional]

       poetry run pre-commit install

1.6 Alternative for steps 1.2-1.5 using `Makefile`

       make set_up

#### 2. Build local repository
This script builds the data repository required to run Dash app, and it is
based on [GDC API](https://gdc.cancer.gov/developers/gdc-application-programming-interface-api)
and [GDC data transfer tool](https://docs.gdc.cancer.gov/Data_Transfer_Tool/Users_Guide/Getting_Started/).
Please note that `FIELDS`, `FILTERS` as well as `GDC TRANSFER TOOL EXECUTABLE`
are declared in `data-processing-pipeline/config.json` file.

Additionally, GDC API requires a maximum `FILES_LIMIT` parameter, to test purposes this parameter should
be a relatively small number e.g. 100 (default). However, in the `production` mode, it should be 100000.

    cd data-processing-pipeline/
    poetry run python run.py

#### Run dash app
Please note that to run app in production mode set `debug: false` in `app/config.json` file. Please remember,
that the app requires an existing local data repository from step 1.

    cd app/
    poetry run python app.py  # development mode
    poetry run gunicorn app:server  # production mode

### Path 2
#### Run app in Docker container (short-path, recommended)
Alternatively, a user may want to run the app in Docker container.
This solution comprises all steps described in the path 1.

    git clone https://github.com/ClinicalEpigeneticsLaboratory/eDAVE.git && cd eDAVE/
    docker build . -t edave # build an image

    # once the image is created you may start the container using the following command
    sudo docker run -p 8000:8000 edave # run container

### Additional information
#### Code quality
To ensure the code quality level we use: *black*, *isort*, *lint* and *bandit*. To run those tools:

    make

or specifically:

    make black
    make isort
    make pylint
    make bandit

#### Tests
To run unit tests open main eDAVE directory and type:

    make tests_data_processing_pipeline # to run data processing pipeline tests
    make tests_app # to run app tests
