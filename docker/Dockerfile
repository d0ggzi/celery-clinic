FROM python

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/app

# Install Poetry
RUN pip install poetry

COPY src/homework ./src/homework
COPY tests ./tests
COPY pyproject.toml poetry.lock ./

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install

EXPOSE 8000