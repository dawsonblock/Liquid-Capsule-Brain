FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-ml.txt .

RUN pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt \
    -r requirements-ml.txt
COPY . .
RUN useradd --create-home --shell /bin/bash agi_user
USER agi_user
EXPOSE 8000
CMD ["python","launch_capsule_brain.py"]
