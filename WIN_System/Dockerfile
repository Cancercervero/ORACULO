FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir openai redis pydantic
CMD ["python", "council_orchestrator.py"]
