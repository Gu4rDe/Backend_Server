#!/bin/bash
set -e

echo "Checking ArcFace model..."
MODEL_PATH="models/arcface.onnx"
MODEL_URL="https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx?download=true"

if [ ! -f "$MODEL_PATH" ]; then
    echo "ArcFace model not found. Downloading..."
    echo "This may take a few minutes (size: ~130 MB)..."
    mkdir -p models
    curl -L -o "$MODEL_PATH" "$MODEL_URL"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to download ArcFace model"
        exit 1
    fi
    echo "Model downloaded successfully"
else
    echo "ArcFace model found at $MODEL_PATH"
fi

echo "Starting Face Recognition API..."
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000