PYTHON ?= python3

.PHONY: verify reproduce figure anonymity clean

verify:
	$(PYTHON) scripts/analysis/validate_package.py
	$(PYTHON) scripts/analysis/check_anonymity.py

reproduce:
	$(PYTHON) scripts/analysis/reproduce_all.py

figure:
	$(PYTHON) scripts/analysis/plot_figure2.py

anonymity:
	$(PYTHON) scripts/analysis/check_anonymity.py

clean:
	rm -rf reproduced/*
	touch reproduced/.gitkeep
