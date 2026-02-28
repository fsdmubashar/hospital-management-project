FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt ./

RUN python -m pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    QT_X11_NO_MITSHM=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libdbus-1-3 \
    libegl1 \
    libgl1 \
    libopengl0 \
    libx11-6 \
    libx11-xcb1 \
    libxext6 \
    libxrender1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libsm6 \
    libice6 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system hospitalgroup \
    && useradd --system --create-home --gid hospitalgroup --shell /usr/sbin/nologin hospitaluser

COPY --from=builder /wheels /wheels
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /tmp/requirements.txt \
    && rm -rf /wheels /tmp/requirements.txt /root/.cache

COPY --chown=hospitaluser:hospitalgroup . .
COPY --chown=hospitaluser:hospitalgroup docker/entrypoint.sh /entrypoint.sh

RUN mkdir -p /app/logs /app/backups /app/reports_output /app/data \
    && touch /app/hospital.db \
    && chown hospitaluser:hospitalgroup /app/hospital.db /app/logs /app/backups /app/reports_output /app/data \
    && chmod 600 /app/hospital.db \
    && chmod 750 /app/logs /app/backups /app/reports_output /app/data \
    && chmod 550 /entrypoint.sh

USER hospitaluser:hospitalgroup

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]
