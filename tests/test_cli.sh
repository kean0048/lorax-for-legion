#!/bin/bash
# Note: execute this file from the project root directory

# setup
rm -rf /var/tmp/beakerlib-*/

function setup_tests {
    # explicitly enable sshd for live-iso b/c it is disabled by default
    # due to security concerns (no root password required)
    sed -i.orig 's/^services.*/services --disabled="network" --enabled="NetworkManager,sshd"/' $1/composer/live-iso.ks
    # explicitly enable logging in with empty passwords via ssh, because
    # the default sshd setting for PermitEmptyPasswords is 'no'
    awk -i inplace "
        /%post/ && FLAG != 2 {FLAG=1}
        /%end/ && FLAG == 1 {print \"sed -i 's/.*PermitEmptyPasswords.*/PermitEmptyPasswords yes/' /etc/ssh/sshd_config\"; FLAG=2}
        {print}" \
        $1/composer/live-iso.ks

    # append a section with additional option on kernel command line to example-http-server blueprint
    # which is used for building of most of the images
    cat >> $BLUEPRINTS_DIR/example-http-server.toml << __EOF__

[customizations.kernel]
append = "custom_cmdline_arg"
__EOF__
}

function teardown_tests {
    mv $1/composer/live-iso.ks.orig $1/composer/live-iso.ks
}

# cloud credentials
if [ -f "~/.config/lorax-test-env" ]; then
    . ~/.config/lorax-test-env
fi

if [ -f "/var/tmp/lorax-test-env" ]; then
    . /var/tmp/lorax-test-env
fi

if [ -z "$CLI" ]; then
    export top_srcdir=`pwd`
    . ./tests/testenv.sh

    BLUEPRINTS_DIR=`mktemp -d '/tmp/composer-blueprints.XXXXX'`
    cp ./tests/pylorax/blueprints/*.toml $BLUEPRINTS_DIR

    SHARE_DIR=`mktemp -d '/tmp/composer-share.XXXXX'`
    cp -R ./share/* $SHARE_DIR
    chmod a+rx -R $SHARE_DIR

    setup_tests $SHARE_DIR
    # start the lorax-composer daemon
    ./src/sbin/lorax-composer --sharedir $SHARE_DIR $BLUEPRINTS_DIR &
else
    export PACKAGE="composer-cli"
    SHARE_DIR="/usr/share/lorax"
    setup_tests $SHARE_DIR
    systemctl restart lorax-composer
fi


# wait for the backend to become ready
tries=0
until curl -m 15 --unix-socket /run/weldr/api.socket http://localhost:4000/api/status | grep 'db_supported.*true'; do
    tries=$((tries + 1))
    if [ $tries -gt 20 ]; then
        exit 1
    fi
    sleep 2
    echo "DEBUG: Waiting for backend API to become ready before testing ..."
done;


if [ -z "$*" ]; then
    # invoke cli/ tests which can be executed without special preparation
    ./tests/cli/test_blueprints_sanity.sh
    ./tests/cli/test_compose_sanity.sh
else
    # execute other cli tests which need more adjustments in the calling environment
    # or can't be executed inside Travis CI
    for TEST in "$@"; do
        $TEST
    done
fi


if [ -z "$CLI" ]; then
    # stop lorax-composer and remove /run/weldr/api.socket
    # only if running against source
    pkill -9 lorax-composer
    rm -f /run/weldr/api.socket
    teardown_tests $SHARE_DIR
else
    systemctl stop lorax-composer
    teardown_tests $SHARE_DIR
    # start lorax-composer again so we can continue with manual or other kinds
    # of testing on the same system
    systemctl start lorax-composer
fi

# look for failures
grep RESULT_STRING /var/tmp/beakerlib-*/TestResults | grep -v PASS && exit 1

# explicit return code for Makefile
exit 0
