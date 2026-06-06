FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY stickers/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY stickers/ .

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
