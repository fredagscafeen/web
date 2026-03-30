FROM python:3.8

RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    texlive-latex-extra \
    latexmk \
    cups \
    rsync \
    gettext \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pip-tools pre-commit

WORKDIR /app
