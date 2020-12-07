FROM ubuntu:20.04
MAINTAINER InAcademia Team, tech@inacademia.org

ARG admin_data_repo
ARG idp_hint_repo

ENV ADMIN_DATA_REPO=$admin_data_repo
ENV IDP_HINT_REPO=$idp_hint_repo

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    wget \
    python3 \
    python3-wget \
    python3-xmltodict \
    ssh \
    rsync
RUN apt clean

#Copy over start and parse script
COPY app/start.sh /tmp/inacademia/start.sh
COPY app/parse.py /tmp/inacademia/parse.py

ENTRYPOINT ["/tmp/inacademia/start.sh"]
# ENTRYPOINT ["/bin/bash"]
