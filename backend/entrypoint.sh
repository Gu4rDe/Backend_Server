#!/bin/bash
set -e

echo "========================================="
echo "  Face Recognition API - Docker Startup"
echo "========================================="
echo ""

# Pre-download insightface models (buffalo_l)
INSIGHTFACE_DIR="${HOME}/.insightface/models/buffalo_l"

if [ ! -d "$INSIGHTFACE_DIR" ]; then
    echo "[INFO] insightface models not found. Pre-downloading buffalo_l..."
    echo "[INFO] This may take a few minutes (size: ~32 MB)..."
    .venv/bin/python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l'); app.prepare(ctx_id=-1, det_size=(640,640))" || {
        echo "[WARN] Failed to pre-download insightface models. They will be downloaded on first request."
    }
else
    echo "[INFO] insightface models found at $INSIGHTFACE_DIR"
fi



# Check .env file
if [ ! -f ".env" ]; then
    echo "[INFO] .env file not found. Creating with generated secrets..."
    SECRET_KEY=$(.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(.venv/bin/python -c "from app.services.crypto import generate_encryption_key; print(generate_encryption_key())")
    INITIAL_CODE=$(.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(16))")

    cat > .env << EOF
DATABASE_URL=sqlite:///./data/faces.db
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
INITIAL_INVITE_CODE=${INITIAL_CODE}
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com
FRONTEND_URL=http://localhost:3000
EOF

    echo "[INFO] .env file created with generated secrets"
    echo "[INFO] INITIAL_INVITE_CODE: ${INITIAL_CODE}"
else
    echo "[INFO] .env file found"
fi

echo ""
echo "[INFO] Starting Face Recognition API on 0.0.0.0:8000..."
echo "========================================="
echo ""

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
