#! /bin/bash
IMAGE_TAG=inacademia/hinting:v1
# cd /home/ubuntu/inacademia-hinting

# Build the docker image if needed
if [[ "$(docker images -q $IMAGE_TAG 2> /dev/null)" == "" ]]; then
  ./build_hinting.sh
fi


echo '##############################################################################################'
echo $(date +"%c")
echo '##############################################################################################'

# Start Hinting
docker run -i \
        -v /etc/passwd:/etc/passwd:ro \
        -v /etc/group:/etc/group:ro \
        -v ${PWD}:/home/ubuntu \
        --mount src=${PWD}/config,target=/tmp/inacademia/config,type=bind \
        --mount source=inacademia_admin_data,target=/tmp/inacademia_admin_data \
        --hostname hinting.inacademia.local \
        $IMAGE_TAG

