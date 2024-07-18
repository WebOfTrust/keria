FROM weboftrust/keri:1.2.0-dev10

WORKDIR /usr/local/var

RUN mkdir keria
COPY . /usr/local/var/keria

WORKDIR /usr/local/var/keria

RUN pip install -r requirements.txt