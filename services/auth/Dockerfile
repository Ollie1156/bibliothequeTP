# syntax=docker/dockerfile:1

# ---------- Étape 1 : "builder" ----------
# Installe les dépendances dans un environnement virtuel isolé.
# Cette étape contient pip, les caches, etc. : elle ne part PAS en production.
FROM python:3.13-slim AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# On copie requirements.txt seul AVANT le code : tant qu'il ne change pas,
# Docker réutilise le cache de cette couche et ne réinstalle rien.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Étape 2 : image finale ----------
# On repart d'une image propre et on ne récupère que le venv déjà prêt.
FROM python:3.13-slim

# Pas de fichiers .pyc, logs affichés immédiatement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Sécurité : un utilisateur sans privilèges (pas root)
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser app ./app

# UID numérique : permet à Kubernetes (runAsNonRoot) de vérifier que ce n'est pas root
USER 10001
EXPOSE 4001

# Docker vérifie régulièrement que le service répond
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4001/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4001"]
