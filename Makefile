uv = uv run

format:
	$(uv) ruff format . && $(uv) ruff check --fix
	@echo "✨ Formatting complete"

check:
	$(uv) basedpyright
	@echo "✨ Checking complete"

mypy:
	$(uv) mypy aiogram_callback_data
	@echo "✨ MyPy complete"

all: format check mypy
