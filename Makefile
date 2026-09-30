.PHONY: install demo test app quality-gate monitor docker-build docker-run

install:
	python -m pip install -r requirements.txt

demo:
	python src/utils/generate_dirty_data.py
	python src/utils/generate_sql_demo.py
	python -m src.monitoring_demo

test:
	pytest -q

app:
	streamlit run app/streamlit_app.py

quality-gate:
	python -m src.quality_gate_cli data/raw/retail_transactions_reference.csv

monitor:
	python -m src.monitoring_cli data/raw/retail_transactions_dirty.csv --reference data/raw/retail_transactions_reference.csv

docker-build:
	docker build -t ai-data-quality-detective .

docker-run:
	docker run --rm -p 8501:8501 ai-data-quality-detective
