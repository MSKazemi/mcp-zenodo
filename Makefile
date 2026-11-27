.PHONY: help setup test lint serve
.DEFAULT_GOAL := help

help: ## Show this help
	@awk -F':.*## ' '/^[a-z]+:.*## / {printf "  make %-7s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install the dependencies (needs uv)
	uv sync

test: ## Run the tests (no Zenodo token or network needed)
	cd mcp_api && uv run python -m unittest discover -s tests

lint: ## Check the code with Ruff
	uvx ruff@0.14.0 check .

serve: ## Run the HTTP service on http://127.0.0.1:8000
	cd mcp_api && uv run python -m server.main
