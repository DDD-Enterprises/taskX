FROM python:3.12-slim@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
WORKDIR /app
RUN useradd -m -r -s /bin/false taskx && chown -R taskx:taskx /app
COPY requirements.lock .
COPY dist/*.whl .
RUN pip install --no-cache-dir -r requirements.lock
RUN pip install --no-cache-dir --no-deps *.whl
USER taskx
ENTRYPOINT ["taskx"]
