FROM python:3.7-slim-buster

WORKDIR /app

RUN apt-get update && \
    apt-get install -y postgresql
RUN apt-get install -y python-psycopg2
RUN apt-get install -y libpq-dev
RUN apt-get install -y gcc

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8000
EXPOSE 5432

CMD ["python3", "app.py"]