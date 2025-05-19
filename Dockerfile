FROM python:3.11-slim 

# Rest of your Dockerfile remains the same
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install psycopg2-binary && \
    python -m pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput