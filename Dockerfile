FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 AS lambda-adapter

FROM python:3.12-slim
# AWS Lambda Web Adapter: lets this same image run on Lambda (it is an extension,
# inert outside Lambda). It waits for /health, then forwards invocations to uvicorn.
COPY --from=lambda-adapter /lambda-adapter /opt/extensions/lambda-adapter
ENV AWS_LWA_PORT=8000 AWS_LWA_READINESS_CHECK_PATH=/health
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LATIN_MORPH_CACHE=/app/.cache
WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY skills/latin-morphology/scripts/latin_morph ./latin_morph
COPY server ./server
# pre-build the lexicon cache so the container starts warm
RUN python -c "from latin_morph.lexicon import get_lexicon; print(len(get_lexicon().lemmas), 'lemmata')"
RUN useradd -r -u 10001 app && chown -R app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
