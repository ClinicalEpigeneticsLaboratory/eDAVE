all: black isort bandit tests_data_processing_pipeline tests_app pylint


set_up:
	@echo "Setting up project"
	pip install poetry
	poetry install
	poetry run pre-commit install

black:
	@echo "Code formatting"
	poetry run black .

isort:
	@echo "Imports sorting"
	poetry run isort .

tests_data_processing_pipeline:
	@echo "Running tests for data processing pipeline"
	cd data-processing-pipeline/ && poetry run python -m pytest tests.py

tests_app:
	@echo "Running tests for app"
	cd app/ && poetry run python -m pytest tests.py

pylint:
	@echo "Code QC"
	poetry run pylint *

bandit:
	@echo "Security check"
	poetry run bandit -r app/ -s B101,B301,B403
