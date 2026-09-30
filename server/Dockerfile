FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY ai ./ai
COPY server ./server

ENV ULTRON_CHECKPOINT=/etc/secrets/ultron_v0_2.pt
ENV ULTRON_TOKENIZER=/etc/secrets/tokenizer_v0_2.json

EXPOSE 10000

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
