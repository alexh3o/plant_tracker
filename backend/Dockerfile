FROM python:3.10-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY . .
RUN pip install fastapi uvicorn requests python-multipart
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
