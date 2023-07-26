ARG BASE_IMAGE=keripy
FROM ${BASE_IMAGE}

WORKDIR /keria
COPY ./ ./
RUN pip install -r requirements.txt

EXPOSE 3901
EXPOSE 3902
EXPOSE 3903

ENV KERI_AGENT_CORS=true

ENTRYPOINT ["keria", "start",  "--config-file", "demo-witness-oobis", "--config-dir", "./scripts"]
