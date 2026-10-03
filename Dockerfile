FROM python:3.11-slim

WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# ULTRON's model code and training data.
COPY ai ./ai
RUN cd ai && ULTRON_CPU_STEPS=300 python train_v0_2.py

# ULTRON's own server and web interface.
COPY server ./server
COPY index.html style.css app.js ./

ENV ULTRON_CHECKPOINT=/app/ai/checkpoints/ultron_v0_2.pt
ENV ULTRON_TOKENIZER=/app/ai/checkpoints/tokenizer_v0_2.json
ENV PYTHONUNBUFFERED=1

EXPOSE 10000

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
