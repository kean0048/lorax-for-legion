#!/bin/bash
# Note: execute this file from the project root directory

# setup
rm -rf /var/tmp/beakerlib-*/
export top_srcdir=`pwd`
. ./tests/testenv.sh

# start the lorax-composer daemon
./src/sbin/lorax-composer --sharedir ./share/ ./tests/pylorax/blueprints/ &

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

# invoke cli/ tests
./tests/cli/test_blueprints_sanity.sh
./tests/cli/test_compose_sanity.sh

# need `losetup`, which needs Docker to be in privileged mode (--privileged),
# which is available only for `docker run`, however we use `docker build`!
# And all of this may not even work on Travis CI so disabling execution for now!
# maybe we will figure out how to execute these two scripts on internal Jenkins instance
#./tests/cli/test_compose_ext4-filesystem.sh
#./tests/cli/test_compose_partitioned-disk.sh

# Stop lorax-composer and remove /run/weldr/api.socket
pkill -9 lorax-composer
rm -f /run/weldr/api.socket

# look for failures
grep RESULT_STRING /var/tmp/beakerlib-*/TestResults | grep -v PASS && exit 1

# explicit return code for Makefile
exit 0
