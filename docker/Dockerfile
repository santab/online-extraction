# Multi-stage build: install deps in a builder stage, ship a slim runtime
# image with skills baked in at build time (never editable at runtime) and
# no build toolchain.

FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml ./
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /install /usr/local
WORKDIR /app
COPY src/ src/
COPY skills/ skills/
COPY profiles/ profiles/

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

USER appuser
# Root filesystem is mounted read-only at deploy time except /tmp — no
# writes belong anywhere under /app; scratch state lives on the checkpointer
# and raw files in object storage, per the architecture doc's backend split.
ENTRYPOINT ["python", "-m", "extraction_agent.runtime.entrypoint"]
