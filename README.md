# ULTRON AI

A personal AI assistant project with a futuristic red-and-black interface and browser-based voice controls.

## Current status

The repository currently contains a static front-end prototype. It includes:

- Responsive red-and-black ULTRON-inspired styling
- A local demo conversation interface
- Browser speech recognition where supported
- A conversation clear button

**Important:** The assistant is currently in demo mode. It is not connected to a live AI model, and its replies are predefined examples. Voice recognition and speech features depend on browser/device support.

## Run it

Open `index.html` in a modern browser, or enable GitHub Pages for this repository and serve the site from the branch and folder containing `index.html` (for example, `main` and `/(root)`).

## Next milestone: secure AI backend

To connect a real model, add a backend service that makes the AI provider request. Keep API keys in the backend host's environment/secrets settings—**never place secret keys in `app.js`, `index.html`, or any public client-side code**. The front end should send messages to your backend endpoint, not directly to a provider using a secret key.

## Project note

This is an independent personal project inspired by a fictional AI concept. It is not an official Marvel product.
