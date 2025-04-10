FROM python:3.13.3-slim
WORKDIR /app
COPY requirements.txt requirements.txt 
RUN pip install --no-cache-dir -r requirements.txt

COPY bin bin
COPY pkg pkg
COPY db.sqlite db.sqlite

EXPOSE 8000

CMD ["python",  "-m", "bin.main"]
