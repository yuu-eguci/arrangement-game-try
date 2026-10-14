FROM python:3.15-slim@sha256:ea4f1f290e071bf7d28199cfb3e09f5dbad31b50e9c32fd58f2f2d7be915f3ae

RUN apt-get update \
    && apt-get install -y --no-install-recommends novnc websockify x11vnc xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -m 1777 /tmp/.X11-unix
COPY docker/index.html /usr/share/novnc/index.html
COPY --from=ghcr.io/astral-sh/uv:0.13@sha256:cdc6093146eb3ff6a40107b38f008b789e050e77ad87865e381d9917da55a168 /uv /usr/local/bin/uv

RUN useradd --create-home player
USER player
WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/home/player/venv \
    PATH=/home/player/venv/bin:$PATH \
    SDL_AUDIODRIVER=dummy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTEST_ADDOPTS="-p no:cacheprovider" \
    RUFF_NO_CACHE=true
COPY --chown=player pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project
COPY --chown=player . .

EXPOSE 6080
ENTRYPOINT ["/app/docker/entrypoint.sh"]
