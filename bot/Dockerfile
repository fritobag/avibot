FROM python:3.10.2

WORKDIR /bot

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0

RUN apt -u update \
    && pip install poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && apt-get install libjpeg-dev zlib1g-dev -y\
    && poetry install --no-interaction

COPY . .
