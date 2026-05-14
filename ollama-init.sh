#!/usr/bin/env bash
set -euo pipefail

LLM_MODELS="${OLLAMA_LLM_MODELS:-qwen2.5:7b-instruct-q4_K_M,qwen2.5:3b-instruct-q4_K_M}"
EMBED_MODELS="${OLLAMA_EMBED_MODELS:-bge-m3}"

/bin/ollama serve &
SERVE_PID=$!

until ollama list >/dev/null 2>&1; do
    sleep 2
done

# Comma-separated list lets us pull multiple LLMs (e.g. a small fast model
# alongside a larger one). OLLAMA_MAX_LOADED_MODELS in compose caps how many
# stay in RAM at once.
IFS=',' read -ra ALL_MODELS <<< "${LLM_MODELS},${EMBED_MODELS}"
for model in "${ALL_MODELS[@]}"; do
    model="${model// /}"
    [ -z "$model" ] && continue
    if ! ollama list | awk 'NR>1 {print $1}' | grep -Fxq "$model"; then
        echo "Pulling $model..."
        ollama pull "$model"
    else
        echo "Model $model already present."
    fi
done

wait "$SERVE_PID"
