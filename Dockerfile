# snaptext in a container: reproducible CLI runs anywhere.
#
#   docker build -t snaptext .
#   docker run --rm -v "$PWD:/data" snaptext file /data/scan.pdf
#
# Scope: file / pdf / watch on mounted volumes. Screen capture and hotkeys
# need a host desktop and are not supported in the container.
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY snaptext ./snaptext

RUN pip install --no-cache-dir .

ENTRYPOINT ["snaptext"]
CMD ["--help"]
