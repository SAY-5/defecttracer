FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gdb && \
    rm -rf /var/lib/apt/lists/* && useradd -m -u 1001 dt
COPY pyproject.toml README.md ./
COPY defecttracer ./defecttracer
RUN pip install --no-cache-dir -e .
USER dt
ENTRYPOINT ["dtrace"]
