FROM python:3.12-slim
WORKDIR /app
COPY server.py gemini_service.py finance.py ./
RUN useradd --create-home wangku
USER wangku
EXPOSE 8080
CMD ["python", "server.py"]
