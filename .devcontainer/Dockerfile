FROM python:3.14.4

RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    texlive-latex-extra \
    latexmk \
    cups \
    rsync \
    gettext \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN pip install --no-cache-dir pip-tools pre-commit

WORKDIR /app
