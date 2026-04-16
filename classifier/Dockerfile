FROM python:3.11-slim
RUN pip install --no-cache-dir \
    pandas==2.2.3 \
    numpy==1.26.4 \
    scikit-learn==1.6.1 \
    joblib==1.4.2 \
    psycopg2-binary==2.9.9
WORKDIR /app
COPY classify.py /app/classify.py
COPY final_models /app/final_models
ENTRYPOINT ["python", "/app/classify.py"]
