FROM python:3.12.6-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libldap2-dev \
    libsasl2-dev \
    libtiff5-dev \
    zlib1g-dev \
    wkhtmltopdf \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/odoo

COPY odoo/requirements.txt .
RUN pip install --no-cache-dir inotify debugpy

EXPOSE 8069

CMD ["python3", "odoo-bin"]