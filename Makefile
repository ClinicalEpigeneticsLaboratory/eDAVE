all: black isort bandit pylint


set_up:
	@echo "Setting up project"
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
