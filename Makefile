.PHONY: build docs

_: check


# Development Environment Setup

pip:
	python -m pip install --upgrade pip

install: install-req
	python -m pip install -e .

install-all: pip
	python -m pip install --upgrade -e . -r requirements.txt -r docs/requirements.txt

install-req: pip
	python -m pip install --upgrade -r requirements.txt

install-req-all: pip
	python -m pip install --upgrade -r requirements.txt -r docs/requirements.txt

install-req-docs: pip
	python -m pip install --upgrade -r docs/requirements.txt

uninstall:
	pip uninstall -y term-image


# Pre-commit Checks and Corrections

check: check-code

py_files := *.py src/ docs/source/conf.py

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

build:
	python -m pip install --upgrade pip
	python -m pip install --upgrade build
	python -m build

clean:
	rm -rf build dist
