#! /bin/bash
IMAGE_TAG=inacademia/hinting:v1

# Build the docker image if needed
if [[ "$(docker images -q $IMAGE_TAG 2> /dev/null)" == "" ]]; then
  docker build -t $IMAGE_TAG .
fi

# find the location of configs in current directory structure
RUN_DIR=$PWD

# Start SVS
docker run -it \
	-v /etc/passwd:/etc/passwd:ro \
	-v /etc/group:/etc/group:ro \
	-v /home/ubuntu:/home/ubuntu \
	--hostname hinting.inacademia.local \
	$IMAGE_TAG
