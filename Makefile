PYTHON ?= python3
VENV_PY ?= .venv/bin/python

.PHONY: test train-ml benchmarks ml-benchmarks snapshot manual-gold-eval pipeline-sample bundle train-camembert spacy-camembert-bench train-camembert-ft camembert-ft-bench train-camembert-ft-v2 camembert-ft-v2-bench e2e-camembert-ft-v2

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

train-camembert:
	$(VENV_PY) scripts/train_camembert.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --model-dir models/camembert --hf-model camembert-base --batch-size 32 --max-length 64 --max-samples 4000

spacy-camembert-bench:
	$(VENV_PY) scripts/run_spacy_camembert_benchmarks.py --python-bin $(VENV_PY) --datasets datasets --places data/places.txt --spacy-model fr_core_news_sm --camembert-model-dir models/camembert --output reports/spacy_camembert_metrics.json

train-camembert-ft:
	$(VENV_PY) scripts/train_camembert_finetune.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --dev-input datasets/dev_input.txt --dev-output datasets/dev_output.txt --target origin --output-dir models/camembert_finetune/origin --hf-model camembert-base --max-length 64 --batch-size 16 --epochs 1 --lr 2e-5 --max-train-samples 4000 --seed 42
	$(VENV_PY) scripts/train_camembert_finetune.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --dev-input datasets/dev_input.txt --dev-output datasets/dev_output.txt --target destination --output-dir models/camembert_finetune/destination --hf-model camembert-base --max-length 64 --batch-size 16 --epochs 1 --lr 2e-5 --max-train-samples 4000 --seed 42

camembert-ft-bench:
	$(VENV_PY) scripts/run_camembert_finetune_benchmarks.py --python-bin $(VENV_PY) --datasets datasets --origin-model-dir models/camembert_finetune/origin --destination-model-dir models/camembert_finetune/destination --output reports/camembert_finetune_metrics.json

train-camembert-ft-v2:
	$(VENV_PY) scripts/train_camembert_finetune.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --dev-input datasets/dev_input.txt --dev-output datasets/dev_output.txt --target origin --output-dir models/camembert_finetune_v2/origin --hf-model camembert-base --max-length 64 --batch-size 16 --epochs 2 --lr 2e-5 --seed 42
	$(VENV_PY) scripts/train_camembert_finetune.py --train-input datasets/train_input.txt --train-output datasets/train_output.txt --dev-input datasets/dev_input.txt --dev-output datasets/dev_output.txt --target destination --output-dir models/camembert_finetune_v2/destination --hf-model camembert-base --max-length 64 --batch-size 16 --epochs 2 --lr 2e-5 --seed 42

camembert-ft-v2-bench:
	$(VENV_PY) scripts/run_camembert_finetune_benchmarks.py --python-bin $(VENV_PY) --datasets datasets --origin-model-dir models/camembert_finetune_v2/origin --destination-model-dir models/camembert_finetune_v2/destination --output reports/camembert_finetune_v2_metrics.json

e2e-camembert-ft-v2:
	$(VENV_PY) scripts/evaluate_end_to_end.py --input datasets/manual/input_starter.csv --nlp-backend camembert-ft --origin-model-dir models/camembert_finetune_v2/origin --destination-model-dir models/camembert_finetune_v2/destination --graph data/graph.json --stops-index data/stops_index.json --stops-areas data/stops_areas.csv --output-csv datasets/manual/e2e_manual_120_camembert_v2.csv --summary reports/e2e_manual_120_camembert_v2_summary.json
