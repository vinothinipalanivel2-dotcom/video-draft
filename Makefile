.PHONY: help install test lint run benchmark clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install core and dev dependencies"
	@echo "  make test       - Run all unit and integration tests"
	@echo "  make lint       - Run code style checks"
	@echo "  make run        - Execute default baseline pipeline"
	@echo "  make benchmark  - Run benchmark suite"
	@echo "  make clean      - Clean build and temporary test artifacts"

install:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	pytest tests/ -v

lint:
	python -m py_compile src/video_draft/*.py

run:
	video-draft run --brief configs/briefs/baseline_16x9.json

benchmark:
	video-draft benchmark --brief configs/briefs/baseline_16x9.json

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').glob('*.egg-info')]"
