all: black isort bandit pylint tests


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

pylint:
	@echo "Code QC"
	poetry run pylint *

bandit:
	@echo "Security check"
	poetry run bandit -r app/

tests:
	@echo "Unit tests"
	cd data-processing-pipeline/ && poetry run python -m pytest tests.py
