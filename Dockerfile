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
RUN /usr/bin/git clone https://github.com/inacademia-development/inacademia-hinting.git /tmp/inacademia/hinting
RUN /usr/bin/git clone https://github.com/inacademia-development/idp_hint.git /tmp/inacademia/hinting/output/idp_hint
# This won't work because at build time the docker has no access to the correct key
# RUN /usr/bin/git clone git@github.com:inacademia-development/idp_hint.git /tmp/inacademia/hinting/output/idp_hint
RUN cd /tmp/inacademia/hinting/output/idp_hint; /usr/bin/git remote add origin-ssh git@github.com:inacademia-development/idp_hint.git

ENTRYPOINT ["/tmp/inacademia/run.sh"]
#ENTRYPOINT ["/bin/bash"]
