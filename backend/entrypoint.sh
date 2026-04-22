#!/bin/bash
set -e

echo "========================================="
echo "  Face Recognition API - Docker Startup"
echo "========================================="
echo ""

# Check ArcFace model
MODEL_PATH="models/arcface.onnx"
MODEL_URL="https://huggingface.co/garavv/arcface-onnx/resolve/main/arc.onnx?download=true"

if [ ! -f "$MODEL_PATH" ]; then
    echo "[INFO] ArcFace model not found. Downloading..."
    echo "[INFO] This may take a few minutes (size: ~130 MB)..."
    mkdir -p models
    if curl -L -o "$MODEL_PATH" "$MODEL_URL"; then
        echo "[INFO] Model downloaded successfully"
    else
        echo "[ERROR] Failed to download ArcFace model"
        exit 1
    fi
else
    echo "[INFO] ArcFace model found at $MODEL_PATH"
fi

echo ""

# Check .env file
if [ ! -f ".env" ]; then
    echo "[INFO] .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "[INFO] .env file created. Please configure SECRET_KEY and INITIAL_INVITE_CODE"
    else
        echo "[WARN] No .env.example found. Using defaults."
    fi
else
    echo "[INFO] .env file found"
fi

echo ""
echo "[INFO] Starting Face Recognition API on 0.0.0.0:8000..."
echo "========================================="
echo ""

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
