FROM python:3.8

RUN apt-get update && apt-get install -y texlive-latex-extra latexmk cups && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV DJANGO_SETTINGS_MODULE=fredagscafeen.settings.htlm5

CMD ["./setup_and_run"]
