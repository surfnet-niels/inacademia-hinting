#!/bin/bash
HINTING_ROOTPATH=/tmp/inacademia
CONFIG_PATH=/tmp/config

echo -e "Removing admin data repo" 
rm -rf /tmp/admin_data_repo

# Note the config path gets included into the docker via volume mounting
echo -e "Setting config path"
ln -s $CONFIG_PATH /tmp/inacademia/hinting/

echo -e "Sourcing config"
source $CONFIG_PATH/hinting.cnf
cd $HINTING_ROOTPATH/hinting

# download eduGAN metadata to input dir
echo -e "Downloading eduGAIN metadata"
/usr/bin/wget http://mds.edugain.org/ -q  -O $HINTING_ROOTPATH/input/edugain.xml
echo -e "Downloading eduGAIN metadata done"

# Pull the latest version of idp_hint data from the git repo
echo -e "Fetching idp_hint data from https://github.com/$IDP_HINT_REPO"
/usr/bin/git clone https://github.com/$IDP_HINT_REPO /tmp/inacademia/output/idp_hint
cd /tmp/inacademia/output/idp_hint; /usr/bin/git remote add origin-ssh git@github.com:$IDP_HINT_REPO

cd $HINTING_ROOTPATH/output/idp_hint/
GIT_SSH_COMMAND='ssh -i /home/ubuntu/.ssh/id_rsa_inacademia' /usr/bin/git pull

# parse the eduGAIN xml, this produces data in the output dir, potentially overwriting data in output/idp_hint
echo -e "Parsing eduGAIN metadata" 
/usr/bin/python $HINTING_ROOTPATH/hinting/parse.py

# commit and push the updated data to git repo.
cd $HINTING_ROOTPATH/output/idp_hint
GIT_SSH_COMMAND='ssh -i /tmp/config/id_rsa_inacademia' /usr/bin/git add --all
GIT_SSH_COMMAND='ssh -i /tmp/config/id_rsa_inacademia' /usr/bin/git commit -am "Updated entities $(date +'%F %T')"
GIT_SSH_COMMAND='ssh -oStrictHostKeyChecking=no -i /tmp/config/id_rsa_inacademia' /usr/bin/git push origin-ssh

# Pull the latest version of the admin_data from the git repo
echo -e "Fetching idp_hint admin data from $ADMIN_DATA_REPO"
mkdir /tmp/admin_data_repo
GIT_SSH_COMMAND='ssh -i /tmp/config/id_rsa_inacademia' /usr/bin/git clone $ADMIN_DATA_REPO /tmp/admin_data_repo/
cd /tmp/admin_data_repo/ 
GIT_SSH_COMMAND='ssh -i /tmp/config/id_rsa_inacademia' /usr/bin/git remote add origin-ssh git@$ADMIN_DATA_REPO

# sync admin data to persistent storage volume and to git repo
echo -e "Syncing admin data to $PERSISTEN_DATA_VOLUME_MOUNTPOINT"
rsync -rtv $HINTING_ROOTPATH/admin/ $PERSISTEN_DATA_VOLUME_MOUNTPOINT
rsync -rtv $HINTING_ROOTPATH/admin/ /tmp/admin_data_repo/
rsync -rtv $HINTING_ROOTPATH/output/idp_hint/display_names.json $PERSISTEN_DATA_VOLUME_MOUNTPOINT

# comit and push the updated admin data to git repo.
echo -e "Pushing admin repo"
cd /tmp/admin_data_repo/
GIT_SSH_COMMAND='ssh -i /tmp/config/id_rsa_inacademia' /usr/bin/git add --all
GIT_SSH_COMMAND='ssh -i /tmp/config/id_rsa_inacademia' /usr/bin/git commit -am "Updated entities $(date +'%F %T')"
GIT_SSH_COMMAND='ssh -oStrictHostKeyChecking=no -i /tmp/config/id_rsa_inacademia' /usr/bin/git push 



