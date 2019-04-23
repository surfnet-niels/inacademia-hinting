#! /bin/bash
IMAGE_TAG=inacademia/hinting:v1

echo '##############################################################################################'
echo $(date +"%c")
echo '##############################################################################################'

source config/hinting.cnf

# As the build command is being called, we assume we need to build a new image.
# To be sure we therefor first remove existign ones
if [[ "$(docker images -q $IMAGE_TAG 2> /dev/null)" != "" ]]; then
  echo "Removing existing $IMAGE_TAG docker container ..."
  docker rmi -f $IMAGE_TAG
fi

echo "Building  docker container $IMAGE_TAG ..."
# Build the docker image
docker build -t $IMAGE_TAG \
    --build-arg CODE_REPO=${CODE_REPO} \
    --build-arg IDP_HINT_REPO=${IDP_HINT_REPO} \
    .
#    --no-cache .

