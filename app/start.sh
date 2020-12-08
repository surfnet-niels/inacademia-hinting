#!/bin/bash
export HINTING_ROOTPATH=/tmp/inacademia
export CONFIG_PATH=$HINTING_ROOTPATH/config
export FEEDS_PATH=$HINTING_ROOTPATH/feeds
export IDP_HINT_PATH=$HINTING_ROOTPATH/idp_hint
export ADMIN_DATA_PATH=$HINTING_ROOTPATH/admin_data/
export ADMIN_HASHES_PATH=$ADMIN_DATA_PATH/hashes
export ADMIN_DATA_REPO_PATH=$HINTING_ROOTPATH/admin_data_repo/

export GIT_SSH_COMMAND="ssh -oStrictHostKeyChecking=no -i $CONFIG_PATH/id_rsa_inacademia"

echo -e "Create directory structure"
mkdir -p $ADMIN_DATA_REPO_PATH
mkdir -p $ADMIN_DATA_PATH
mkdir -p $ADMIN_HASHES_PATH
mkdir -p $IDP_HINT_PATH
mkdir -p $FEEDS_PATH

# Make git happy
/usr/bin/git config --global push.default matching
/usr/bin/git config --global user.name "InAcademia OPS team"
/usr/bin/git config --global user.email tech@inacademia.org

# Pull the latest version of idp_hint data from the git repo
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
echo -e "Fetching idp_hint data from $IDP_HINT_REPO"
/usr/bin/git clone $IDP_HINT_REPO $IDP_HINT_PATH | /usr/bin/git -C $IDP_HINT_PATH pull
/usr/bin/git -C $IDP_HINT_PATH pull

# Pull the latest version of the admin_data from the git repo
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
echo -e "Fetching idp_hint admin data from $ADMIN_DATA_REPO"
/usr/bin/git clone $ADMIN_DATA_REPO $ADMIN_DATA_REPO_PATH | /usr/bin/git -C $ADMIN_DATA_REPO_PATH pull

# parse the eduGAIN xml, this produces data in the output dir, potentially overwriting data in idp_hint
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
/usr/bin/python3 $HINTING_ROOTPATH/parse.py

# commit and push the updated data to git repo.
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
echo -e "Updating IdP Hints"
# Explicitly update the date on the README in case we had no other commits (tis way we can check if the mechanism is still working...
/usr/bin/git -C $IDP_HINT_PATH add --all
/usr/bin/git -C $IDP_HINT_PATH commit --allow-empty -am "Updated entities $(date +'%F %T')"
/usr/bin/git -C $IDP_HINT_PATH push

# sync admin data to persistent storage volume and to git repo
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
echo -e "Syncing admin data to $ADMIN_DATA_PATH"
rsync -rtv $ADMIN_DATA_PATH $ADMIN_DATA_REPO_PATH
rsync -rtv $IDP_HINT_PATH/display_names.json $ADMIN_DATA_PATH

# comit and push the updated admin data to git repo.
echo -e "+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+"
echo -e "Pushing data to admin repo"
/usr/bin/git -C $ADMIN_DATA_REPO_PATH add --all
/usr/bin/git -C $ADMIN_DATA_REPO_PATH commit --allow-empty -am "Updated entities $(date +'%F %T')"
/usr/bin/git -C $ADMIN_DATA_REPO_PATH push

