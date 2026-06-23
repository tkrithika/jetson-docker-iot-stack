FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY simulate.py .

CMD ["python", "simulate.py"]
