# Minimal makefile for Sphinx documentation

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAPIDOC  = sphinx-apidoc
BUILDDIR      = _build
SOURCEDIR     = .
PYTHON_SOURCE_PATH = ../src

.PHONY: help clean html apidoc

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  apidoc     to generate rst files from docstrings"
	@echo "  clean      to remove generated files"

clean:
	rm -rf $(BUILDDIR)
	rm -f modules.rst src*.rst

apidoc:
	$(SPHINXAPIDOC) -o $(SOURCEDIR) -f -e --module-first $(PYTHON_SOURCE_PATH)
