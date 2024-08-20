##
## Documentation 📚
## -------------
##
.PHONY: serve-doc
.SILENT: serve-doc
serve-doc: ## serve documentation
	 docker run --rm -it -p 8000:8000 -v ${PWD}:/docs squidfunk/mkdocs-material

.PHONY: deploy-doc
.SILENT: deploy-doc
deploy-doc: ## a
	mkdocs gh-deploy
