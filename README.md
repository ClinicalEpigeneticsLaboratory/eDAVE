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
[go to the app](https://edave.pum.edu.pl/)

#### How to start
1. make sure that You have python >= 3.8 installed
2. install [poetry](https://python-poetry.org/) dependency manager

       pip install poetry

3. clone repository

       git clone https://github.com/ClinicalEpigeneticsLaboratory/eDAVE.git

4. open project directory and install required dependencies

       poetry install

5. install pre-commit [optional]

       poetry run pre-commit install

6. Alternative for steps *2*, *4* and *5* using `Makefile`

       make set_up

#### Build local repository
This script builds the data repository required to run Dash app, and it is
based on [GDC API](https://gdc.cancer.gov/developers/gdc-application-programming-interface-api)
and [GDC data transfer tool](https://docs.gdc.cancer.gov/Data_Transfer_Tool/Users_Guide/Getting_Started/).
Please note that `FIELDS`, `FILTERS` as well as `GDC TRANSFER TOOL EXECUTABLE`
are declared in `data-processing-pipeline/config.json` file.

Additionally, GDC API requires a maximum `FILES_LIMIT` parameter, to test purposes this parameter should
be a relatively small number e.g. 100 (default). However, in production mode, it should be 100000.

    cd data-processing-pipeline/
    poetry run python run.py

#### Run dash app
Please note that to run app in production mode set `debug: false` in `app/config.json` file. Moreover,
the app requires an existing local data repository.

    cd app/
    poetry run python app.py  # development mode
    poetry run gunicorn app:server  # production mode

#### Run in Docker container
Alternatively, a user may want to run the app in Docker container. This solution comprises all above-mentioned steps.

    docker build . -t edave # build an image
    sudo docker run -p 8000:8000 edave # run container

#### Code quality
To ensure the code quality level we use: *black*, *isort*, *lint* and *bandit*. To run those tools:

    make

or specifically:

    make black
    make isort
    make pylint
    make bandit
