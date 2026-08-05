.PHONY: run install clean

# Run the main application using uv
run:
	uv run Graphic/main.py

# Install or sync project dependencies using uv
install:
	uv sync

# Clean up Python cache and compiled files
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +