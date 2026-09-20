PYTHON ?= .venv/bin/python

.PHONY: install install-all test data-fd001 data-fd004 eda-fd001 eda-fd004 train-xgboost-fd001 train-xgboost-fd004 experiment-fd001 experiment-fd004 serve

install:
	uv sync --python 3.11 --extra dev

install-all:
	uv sync --python 3.11 --extra dev --extra models --extra api

test:
	env -u OMP_NUM_THREADS $(PYTHON) -m pytest

data-fd001:
	$(PYTHON) scripts/download_cmapss.py --subset FD001

data-fd004:
	$(PYTHON) scripts/download_cmapss.py --subset FD004

eda-fd001:
	$(PYTHON) -m rul_pm.cli eda --config configs/fd001.yaml

eda-fd004:
	$(PYTHON) -m rul_pm.cli eda --config configs/fd004.yaml

train-xgboost-fd001:
	$(PYTHON) -m rul_pm.cli train --config configs/fd001.yaml --model xgboost

train-xgboost-fd004:
	$(PYTHON) -m rul_pm.cli train --config configs/fd004.yaml --model xgboost

experiment-fd001:
	$(PYTHON) -m rul_pm.cli experiment --config configs/fd001.yaml

experiment-fd004:
	$(PYTHON) -m rul_pm.cli experiment --config configs/fd004.yaml

serve:
	$(PYTHON) -m uvicorn rul_pm.api.app:create_app --factory --host 127.0.0.1 --port 8000
