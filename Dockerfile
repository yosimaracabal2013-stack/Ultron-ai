FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY ai ./ai
RUN cd ai && ULTRON_CPU_STEPS=300 python train_v0_2.py
COPY server ./server

ENV ULTRON_CHECKPOINT=/app/ai/checkpoints/ultron_v0_2.pt
ENV ULTRON_TOKENIZER=/app/ai/checkpoints/tokenizer_v0_2.json

EXPOSE 10000

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
