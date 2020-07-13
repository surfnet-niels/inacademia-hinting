#! /bin/bash
IMAGE_TAG=inacademia/hinting:v1
cd /home/niels/dev/InAcademia/inacademia-hinting

# Build the docker image if needed
if [[ "$(docker images -q $IMAGE_TAG 2> /dev/null)" == "" ]]; then
  ./build_hinting.sh
fi


echo '##############################################################################################'
echo $(date +"%c")
echo '##############################################################################################'

# Start SVS
docker run -ti \
        -v /etc/passwd:/etc/passwd:ro \
        -v /etc/group:/etc/group:ro \
        -v /home/ubuntu:/home/ubuntu \
        --mount src=/home/niels/dev/InAcademia/inacademia-hinting/config,target=/tmp/inacademia/config,type=bind \
        --mount source=inacademia_admin_data,target=/tmp/inacademia_admin_data \
        --hostname hinting.inacademia.local \
        $IMAGE_TAG

