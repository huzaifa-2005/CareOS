FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries=10 -r requirements.txt

COPY . .

EXPOSE 8000

COPY startup.sh .
RUN chmod +x startup.sh
CMD ["./startup.sh"]