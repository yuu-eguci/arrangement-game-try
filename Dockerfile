FROM python:3.15-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends novnc websockify x11vnc xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -m 1777 /tmp/.X11-unix
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv

RUN useradd --create-home player
USER player
WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/home/player/venv \
    PATH=/home/player/venv/bin:$PATH \
    SDL_AUDIODRIVER=dummy
COPY --chown=player pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-install-project
COPY --chown=player . .

EXPOSE 6080
ENTRYPOINT ["/app/docker/entrypoint.sh"]
