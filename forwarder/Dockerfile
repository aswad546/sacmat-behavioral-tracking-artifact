FROM python:3.11-slim
RUN pip install --no-cache-dir psycopg2-binary==2.9.9 requests==2.32.3
WORKDIR /app
COPY visiblev8-crawler/resend_script_ids.py /app/resend_script_ids.py
ENTRYPOINT ["python", "resend_script_ids.py"]
