FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings
WORKDIR /app/apps/api
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
    && groupadd --gid 10001 tagger && useradd --uid 10001 --gid tagger --no-create-home tagger \
    && mkdir -p /data/blobs /data/static && chown -R tagger:tagger /data
COPY apps/api/ /app/apps/api/
COPY tools/foundation/ /app/tools/foundation/
COPY LICENSE /app/LICENSE
USER 10001:10001
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--error-logfile", "-"]
