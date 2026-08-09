FROM eclipse-temurin:17-jre-jammy

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    FLOWPROOF_TRANSPORT=http \
    FLOWPROOF_HOST=0.0.0.0 \
    FLOWPROOF_PORT=8000 \
    FLOWPROOF_RUNS_DIR=/data/runs

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://get.nextflow.io | bash \
    && mv nextflow /usr/local/bin/nextflow \
    && chmod +x /usr/local/bin/nextflow

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY pipelines ./pipelines

RUN pip3 install --no-cache-dir .

RUN mkdir -p /data/runs

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["flowproof"]
