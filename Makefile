all: black pylint bandit

app_repo="app/"
pipeline_repo="data-processing-pipeline/"

set_up:
	@echo "Setting up project"
	poetry install

black:
	@echo "Code formatting"
	poetry run black .

pylint:
	@echo "Code QC"
	poetry run pylint $(app_repo) $(pipeline_repo)

bandit:
	@echo "Security check"
	poetry run bandit -r $(app_repo)

