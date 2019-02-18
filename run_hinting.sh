
#! /bin/bash
IMAGE_TAG=inacademia/hinting:v1

echo '##############################################################################################'
echo $(date +"%c")
echo '##############################################################################################'

# Start SVS
docker run -it \
	-v /etc/passwd:/etc/passwd:ro \
	-v /etc/group:/etc/group:ro \
	-v /home/ubuntu:/home/ubuntu \
	--mount src="$(pwd)/config",target=/tmp/config,type=bind \
	--mount source=inacademia_admin_data,target=/tmp/inacademia_admin_data \
	--hostname hinting.inacademia.local \
	$IMAGE_TAG
