FROM weboftrust/keri:1.1.17

WORKDIR /usr/local/var

RUN mkdir keria
COPY . /usr/local/var/keria

WORKDIR /usr/local/var/keria

RUN pip install -r requirements.txt