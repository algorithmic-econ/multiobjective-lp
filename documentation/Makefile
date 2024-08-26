##
## Documentation 📚
## -------------
##
.PHONY: serve-doc
.SILENT: serve-doc
serve-doc: ## serve documentation with docker
	 docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material

.PHONY: serve-doc-local
.SILENT: serve-doc-local
serve-doc-local: ## serve documentation directly
	mkdocs serve --verbose

.PHONY: deploy-doc
.SILENT: deploy-doc
deploy-doc: ## a
	mkdocs gh-deploy
