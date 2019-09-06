#!/bin/bash
# Note: execute this file from the project root directory

#####
#
# Builds live-iso image and test it with QEMU-KVM
#
#####

set -e

. /usr/share/beakerlib/beakerlib.sh
. $(dirname $0)/lib/lib.sh

CLI="${CLI:-./src/bin/composer-cli}"

rlJournalStart
    rlPhaseStartSetup
        rlAssertExists $QEMU_BIN

        OPTIONAL_REPO="/etc/yum.repos.d/rhel7-rel-eng-optional.repo"

        if [ ! -f "$OPTIONAL_REPO" ]; then
        cat > $OPTIONAL_REPO << __EOF__
[rhel7-rel-eng-optional]
gpgcheck=0
enabled=1
skip_if_unavailable=0
name=rhel7-rel-eng-optional
baseurl=http://download-node-02.eng.bos.redhat.com/rhel-7/rel-eng/latest-RHEL-7/compose/Server-optional/\$basearch/os/
__EOF__
        fi

    rlPhaseEnd

    rlPhaseStartTest "compose start"
        rlAssertEquals "SELinux operates in enforcing mode" "$(getenforce)" "Enforcing"

        # NOTE: live-iso.ks explicitly disables sshd but test_cli.sh enables it
        UUID=`$CLI compose start example-http-server live-iso`
        rlAssertEquals "exit code should be zero" $? 0

        UUID=`echo $UUID | cut -f 2 -d' '`
    rlPhaseEnd

    rlPhaseStartTest "compose finished"
        wait_for_compose $UUID

        rlRun -t -c "$CLI compose image $UUID"
        IMAGE="$UUID-live.iso"
    rlPhaseEnd

    rlPhaseStartTest "Start VM instance"
        boot_image "-boot d -cdrom $IMAGE" 120
    rlPhaseEnd

    rlPhaseStartTest "Verify VM instance"
        # run generic tests to verify the instance
        ROOT_ACCOUNT_LOCKED=0 verify_image liveuser localhost "-p $SSH_PORT"
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "killall -9 $(basename $QEMU_BIN)"
        rlRun -t -c "$CLI compose delete $UUID"
        rlRun -t -c "rm -rf $IMAGE $OPTIONAL_REPO"
    rlPhaseEnd

rlJournalEnd
rlJournalPrintText
