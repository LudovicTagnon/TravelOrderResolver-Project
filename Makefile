PYTHON ?= python3

.PHONY: test train-ml benchmarks ml-benchmarks snapshot manual-gold-eval pipeline-sample bundle

test:
	$(PYTHON) -m unittest discover -s tests

train-ml:
	$(PYTHON) scripts/train_ml.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --model-dir models

benchmarks:
	$(PYTHON) scripts/run_benchmarks.py --datasets datasets --places data/places.txt --output reports/metrics.json

ml-benchmarks:
	$(PYTHON) scripts/run_ml_benchmarks.py --datasets datasets --model-dir models --output reports/ml_metrics.json

snapshot:
	$(PYTHON) scripts/run_snapshot.py --datasets datasets --reports reports --model-dir models --places data/places.txt --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --manual-input datasets/manual/input_starter.csv --manual-output datasets/manual/output_gold_120.csv --output reports/snapshot.json --markdown-output reports/snapshot.md

manual-gold-eval:
	$(PYTHON) scripts/run_manual_gold_eval.py --input datasets/manual/input_starter.csv --gold-output datasets/manual/output_gold_120.csv --places data/places.txt --model-dir models --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --reports reports --datasets datasets

pipeline-sample:
	$(PYTHON) scripts/run_pipeline.py students_project/sample_nlp_input.txt --places data/places.txt --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --output-nlp students_project/sample_pipeline_nlp_output.txt --output-path students_project/sample_pipeline_path_output.txt

bundle:
	$(PYTHON) scripts/build_submission_bundle.py --output-dir deliverables/submission_bundle --manifest deliverables/submission_bundle/manifest.json
