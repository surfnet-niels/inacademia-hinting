FROM ubuntu:16.04
MAINTAINER InAcademia Team, tech@inacademia.org

ARG CODE_REPO=inacademia-development/inacademia-hinting.git
ARG IDP_HINT_REPO=inacademia-development/idp_hint.git

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    wget \
    python \
    python-xmltodict \
    ssh \
    rsync
RUN apt clean

#Copy over start and parse script
COPY app/start.sh /tmp/inacademia/start.sh
COPY app/parse.py /tmp/inacademia/hinting/parse.py

# create input and output directories
RUN mkdir /tmp/inacademia/input
RUN mkdir /tmp/inacademia/output
RUN mkdir /tmp/inacademia/admin

ENTRYPOINT ["/tmp/inacademia/start.sh"]
#ENTRYPOINT ["/bin/bash"]

