FROM ubuntu:16.04
MAINTAINER InAcademia Team, tech@inacademia.org

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    wget \
    python \
    python-xmltodict \
    ssh
RUN apt clean


COPY run.sh /tmp/inacademia/run.sh
RUN /usr/bin/git clone https://github.com/surfnet-niels/inacademia-hinting.git /tmp/inacademia/hinting
RUN /usr/bin/git clone git@github.com:surfnet-niels/idp_hint.git /tmp/inacademia/hinting/output/idp_hint

ENTRYPOINT ["/tmp/inacademia/run.sh"]
# ENTRYPOINT ["/bin/bash"]
