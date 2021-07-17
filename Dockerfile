# Pull base image
FROM python:3.9.1-alpine

# Set env vars
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work dir
WORKDIR /code

# install psycopg2 dependencies
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

# install Pillow dependencies
RUN apk add jpeg-dev zlib-dev

# install PyMuPDF dependencies
# libc-dev
RUN apk add mupdf-dev jbig2dec openjpeg-dev harfbuzz-dev && ln -s /usr/lib/libjbig2dec.so.0 /usr/lib/libjbig2dec.so

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /code/