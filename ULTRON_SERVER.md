# ULTRON Standalone Server

ULTRON can run as one self-hosted application: the FastAPI server, custom Transformer model, tokenizer, memory API, and web interface live in this repository.

## Architecture

Phone/browser -> ULTRON web interface -> ULTRON FastAPI server -> ULTRON custom Transformer + tokenizer + local project memory.

There is no ChatGPT, Claude, or Gemini inference API in this server.

## Run with Docker

Build and start:

    docker build -t ultron .
    docker run --rm -p 10000:10000 ultron

Then open:

    http://localhost:10000

The container trains the bundled v0.2 checkpoint during the image build if the checkpoint is not already supplied.

## Run without Docker

Install the packages in `server/requirements.txt`, make sure the model checkpoint/tokenizer exist under `ai/checkpoints/`, then run:

    uvicorn server.main:app --host 0.0.0.0 --port 10000

The server exposes the UI at `/`, chat at `/chat`, health at `/health`, state at `/state`, and server ownership information at `/server-info`.

## Important distinction

This repository contains the server software and model. A server still needs a physical or virtual machine to execute it. Hosting it on a third-party platform means that platform supplies the machine; it does not change the software into their AI.

For a fully owner-controlled setup, run this container on hardware you control and keep it private unless you intentionally configure secure remote access.
