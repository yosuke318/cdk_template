FROM python:3.11

WORKDIR /app

RUN apt-get update && apt-get install -y nodejs npm

COPY requirements.txt requirements.txt
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x app.py

CMD ["python3", "app.py"]