.PHONY: build docs

_: check


# Development Environment Setup

pip:  # Upgrade pip
	python -m pip install --upgrade pip

# # [Un]Install Package

install: pip  # Install package
	python -m pip install .

install-dev: pip  # Install package in develop/editable mode
	python -m pip install -e .

uninstall: pip  # Uninstall package
	python -m pip uninstall --yes termvisage

# # Install Dev/Doc Dependencies

req: pip  # Install dev dependencies
	python -m pip install --upgrade -r requirements.txt

req-doc: pip  # Install doc dependencies
	python -m pip install --upgrade -r docs/requirements.txt

req-all: req req-doc

# # Install Dev/Doc Dependencies and Package

dev: req install-dev

dev-doc: req-doc install-dev

dev-all: req-all install-dev


# Pre-commit Checks and Corrections

check: check-code

py_files := src/ docs/source/conf.py

## Code Checks

check-code: lint check-format check-imports

lint:
	flake8 $(py_files) && echo

check-format:
	black --check --diff --color $(py_files) && echo

check-imports:
	isort --check --diff --color $(py_files) && echo

## Code Corrections

format:
	black $(py_files)

imports:
	isort $(py_files)


# Building the Docs

docs:
	cd docs/ && make html

clean-docs:
	cd docs/ && make clean


# Packaging

build: pip
	python -m pip install --upgrade build
	python -m build

clean:
	rm -rf build dist
