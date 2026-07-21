#!/bin/bash
python -m app.services.faiss_builder
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}