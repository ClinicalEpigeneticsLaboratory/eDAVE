![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)
![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)

![Ubuntu 20.04](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

### eDAVE - extension for [GDC Data Analysis, Visualization, and Exploration (DAVE) Tools](https://gdc.cancer.gov/analyze-data/gdc-dave-tools)


#### Goal
The goal of this project is to provide GUI to analyse, visualize and explore datasets from **GDC** (Genomic Data Commons).
This project contains two components:

```
- data-processing-pipeline/ -> implements data processing pipeline to build local data repository.
- app/ -> implements Dash-based app which is an interface to local data repository.
```

#### Contact
jan.binkowski[at]pum.edu.pl

#### App
www.www.www

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

6. steps `4` and `5` are also implemented in `Makefile` [optional]

         make set_up


#### Build local repository
This script builds the data repository required to run Dash app, and it is
based on [GDC API](https://gdc.cancer.gov/developers/gdc-application-programming-interface-api)
and [GDC data transfer tool](https://docs.gdc.cancer.gov/Data_Transfer_Tool/Users_Guide/Getting_Started/).
Please note that `FIELDS`, `FILTERS`, `FILES_LIMIT` as well as `GDC TRANSFER TOOL EXECUTABLE`
are declared in `data-processing-pipeline/config.json` file.

Please note that GDC API requires a maximum `FILES_LIMIT` parameter, to test purposes this parameter should
be a relatively small number e.g. 100 (default). However, in production mode, it should be 100000.

      cd data-processing-pipeline/
      poetry run python run.py


#### Run dash app
To start data exploration. Please note that to run app in production mode set `debug: false` in `app/config.json`
file.

      cd app/
      poetry run python app.py


#### Code quality
To ensure the code quality level we use: *black*, *isort*, *lint* and *bandit*. To run those tools:

      make


or specifically:

    make black
    make isort
    make pylint
    make bandit
