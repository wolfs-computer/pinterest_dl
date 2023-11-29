VENV = ./venv
VENV_BIN = $(VENV)/bin
PYTHON = $(VENV_BIN)/python3
# PIP = $(VENV_BIN)/pip

SHELL = /bin/bash


.PHONY: run clean activate

default: run


run: $(VENV)/bin/activate
	@$(PYTHON) -m pinterest_dl


build: pyproject.toml
	rm -rf dist
	python3 -m build

deploy: dist/*
	python3 -m twine upload --repository testpypi dist/*
