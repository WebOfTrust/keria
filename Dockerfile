FROM build-keipy

WORKDIR /keria
COPY ./ ./
RUN pip install -r requirements.txt

WORKDIR /keripy
RUN pip install -e .

WORKDIR /keria
RUN mkdir -p /keria/scripts/keri/cf
COPY ./config/keria/scripts/keri/cf/demo-witness-oobis.json /keria/scripts/keri/cf/demo-witness-oobis.json

EXPOSE 3901
EXPOSE 3902
EXPOSE 3903

ENV KERI_AGENT_CORS=true

ENTRYPOINT ["keria", "start",  "--config-file", "demo-witness-oobis", "--config-dir", "./scripts"]
