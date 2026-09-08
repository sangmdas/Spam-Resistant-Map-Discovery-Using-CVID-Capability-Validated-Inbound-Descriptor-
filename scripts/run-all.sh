#!/usr/bin/env sh
set -eu
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python examples/house_rental_flow.py
PYTHONPATH=src python tools/benchmark.py --iterations "${1:-50000}"
