# Python asosiy image-ni tanlaymiz
FROM python:3.11-slim

# Muhit o'zgaruvchilarini sozlaymiz
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Ishchi katalogni yaratamiz
WORKDIR /app

# Tizim paketlarini o'rnatamiz (psycopg2 uchun kerak bo'lishi mumkin)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Bog'liqliklarni nusxalaymiz va o'rnatamiz
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Loyiha fayllarini nusxalaymiz
COPY . /app/

# Portni ochamiz
EXPOSE 8000

# Serverni ishga tushirish buyrug'i
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
