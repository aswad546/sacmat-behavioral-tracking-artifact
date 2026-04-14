FROM python:3.11-slim
RUN pip install --no-cache-dir pymongo==4.6.3
COPY seed_mongo.py /seed/seed_mongo.py
COPY mongo_landscape_seed.json /seed/mongo_landscape_seed.json
WORKDIR /seed
ENTRYPOINT ["python", "seed_mongo.py"]
