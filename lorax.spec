# NOTE: This specfile is generated from upstream at https://github.com/rhinstaller/lorax
# NOTE: Please submit changes as a pull request
%define debug_package %{nil}

Name:           lorax
Version:        32.3
Release:        1%{?dist}
Summary:        Tool for creating the anaconda install images

License:        GPLv2+
URL:            https://github.com/weldr/lorax
# To generate Source0 do:
# git clone https://github.com/weldr/lorax
# git checkout -b archive-branch lorax-%%{version}-%%{release}
# tito build --tgz
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3-devel

Requires:       lorax-templates

Requires:       GConf2
Requires:       cpio
Requires:       device-mapper
Requires:       dosfstools
Requires:       e2fsprogs
Requires:       findutils
Requires:       gawk
Requires:       xorriso
Requires:       glib2
Requires:       glibc
Requires:       glibc-common
Requires:       gzip
Requires:       isomd5sum
Requires:       module-init-tools
Requires:       parted
Requires:       squashfs-tools >= 4.2
Requires:       util-linux
Requires:       xz-lzma-compat
Requires:       xz
Requires:       pigz
Requires:       pbzip2
Requires:       dracut >= 030
Requires:       kpartx

# Python modules
Requires:       libselinux-python3
Requires:       python3-mako
Requires:       python3-kickstart >= 3.19
Requires:       python3-dnf >= 3.2.0
Requires:       python3-librepo
Requires:       python3-pycdlib

%if 0%{?fedora}
# Fedora specific deps
%ifarch x86_64
Requires:       hfsplus-tools
%endif
%endif

%ifarch %{ix86} x86_64
Requires:       syslinux >= 6.03-1
Requires:       syslinux-nonlinux >= 6.03-1
%endif

%ifarch ppc64le
Requires:       grub2
Requires:       grub2-tools
%endif

%ifarch s390 s390x
Requires:       openssh
%endif

%ifarch %{arm}
Requires:       uboot-tools
%endif

# Moved image-minimizer tool to lorax
Provides:       appliance-tools-minimizer = %{version}-%{release}
Obsoletes:      appliance-tools-minimizer < 007.7-3

%description
Lorax is a tool for creating the anaconda install images.

It also includes livemedia-creator which is used to create bootable livemedia,
including live isos and disk images. It can use libvirtd for the install, or
Anaconda's image install feature.

%package docs
Summary: Lorax html documentation
Requires: lorax = %{version}-%{release}

%description docs
Includes the full html documentation for lorax, livemedia-creator, lorax-composer and the
pylorax library.

%package lmc-virt
Summary:  livemedia-creator libvirt dependencies
Requires: lorax = %{version}-%{release}
Requires: qemu

# Fedora edk2 builds currently only support these arches
%ifarch %{ix86} x86_64 %{arm} aarch64
Requires: edk2-ovmf
%endif
Recommends: qemu-kvm

%description lmc-virt
Additional dependencies required by livemedia-creator when using it with qemu.

%package lmc-novirt
Summary:  livemedia-creator no-virt dependencies
Requires: lorax = %{version}-%{release}
Requires: anaconda-core
Requires: anaconda-tui
Requires: system-logos

%description lmc-novirt
Additional dependencies required by livemedia-creator when using it with --no-virt
to run Anaconda.

%package templates-generic
Summary:  Generic build templates for lorax and livemedia-creator
Requires: lorax = %{version}-%{release}
Provides: lorax-templates = %{version}-%{release}

%description templates-generic
Lorax templates for creating the boot.iso and live isos are placed in
/usr/share/lorax/templates.d/99-generic

%package composer
Summary: Lorax Image Composer API Server
# For Sphinx documentation build
BuildRequires: python3-flask python3-gobject libgit2-glib python3-toml python3-semantic_version

Requires: lorax = %{version}-%{release}
Requires(pre): /usr/bin/getent
Requires(pre): /usr/sbin/groupadd
Requires(pre): /usr/sbin/useradd

Requires: python3-toml
Requires: python3-semantic_version
Requires: libgit2
Requires: libgit2-glib
Requires: python3-flask
Requires: python3-gevent
Requires: anaconda-tui >= 29.19-1
Requires: qemu-img
Requires: tar
Requires: python3-rpmfluff
Requires: git
Requires: xz
Requires: createrepo_c
Requires: python3-ansible-runner
# For AWS playbook support
Requires: python3-boto3

%{?systemd_requires}
BuildRequires: systemd

%description composer
lorax-composer provides a REST API for building images using lorax.

%package -n composer-cli
Summary: A command line tool for use with the lorax-composer API server

# From Distribution
Requires: python3-urllib3
Requires: python3-toml

%description -n composer-cli
A command line tool for use with the lorax-composer API server. Examine blueprints,
build images, etc. from the command line.

%prep
%setup -q -n %{name}-%{version}

%build

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT mandir=%{_mandir} install

# Install example blueprints from the test suite.
# This path MUST match the lorax-composer.service blueprint path.
mkdir -p $RPM_BUILD_ROOT/var/lib/lorax/composer/blueprints/
for bp in example-http-server.toml example-development.toml example-atlas.toml; do
    cp ./tests/pylorax/blueprints/$bp $RPM_BUILD_ROOT/var/lib/lorax/composer/blueprints/
done

%pre composer
getent group weldr >/dev/null 2>&1 || groupadd -r weldr >/dev/null 2>&1 || :
getent passwd weldr >/dev/null 2>&1 || useradd -r -g weldr -d / -s /sbin/nologin -c "User for lorax-composer" weldr >/dev/null 2>&1 || :

%post composer
%systemd_post lorax-composer.service
%systemd_post lorax-composer.socket

%preun composer
%systemd_preun lorax-composer.service
%systemd_preun lorax-composer.socket

%postun composer
%systemd_postun_with_restart lorax-composer.service
%systemd_postun_with_restart lorax-composer.socket

%files
%defattr(-,root,root,-)
%license COPYING
%doc AUTHORS
%doc docs/composer-cli.rst docs/lorax.rst docs/livemedia-creator.rst docs/product-images.rst
%doc docs/lorax-composer.rst
%doc docs/*ks
%{python3_sitelib}/pylorax
%{python3_sitelib}/*.egg-info
%{_sbindir}/lorax
%{_sbindir}/mkefiboot
%{_sbindir}/livemedia-creator
%{_sbindir}/mkksiso
%{_bindir}/image-minimizer
%{_bindir}/mk-s390-cdboot
%dir %{_sysconfdir}/lorax
%config(noreplace) %{_sysconfdir}/lorax/lorax.conf
%dir %{_datadir}/lorax
%{_mandir}/man1/lorax.1*
%{_mandir}/man1/livemedia-creator.1*
%{_mandir}/man1/mkksiso.1*
%{_tmpfilesdir}/lorax.conf

%files docs
%doc docs/html/*

%files lmc-virt

%files lmc-novirt

%files templates-generic
%dir %{_datadir}/lorax/templates.d
%{_datadir}/lorax/templates.d/*

%files composer
%config(noreplace) %{_sysconfdir}/lorax/composer.conf
%{python3_sitelib}/pylorax/api/*
%{python3_sitelib}/lifted/*
%{_sbindir}/lorax-composer
%{_unitdir}/lorax-composer.service
%{_unitdir}/lorax-composer.socket
%dir %{_datadir}/lorax/composer
%{_datadir}/lorax/composer/*
%{_datadir}/lorax/lifted/*
%{_tmpfilesdir}/lorax-composer.conf
%dir %attr(0771, root, weldr) %{_sharedstatedir}/lorax/composer/
%dir %attr(0771, root, weldr) %{_sharedstatedir}/lorax/composer/blueprints/
%attr(0771, weldr, weldr) %{_sharedstatedir}/lorax/composer/blueprints/*
%{_mandir}/man1/lorax-composer.1*

%files -n composer-cli
%{_bindir}/composer-cli
%{python3_sitelib}/composer/*
%{_sysconfdir}/bash_completion.d/composer-cli
%{_mandir}/man1/composer-cli.1*

%changelog
* Tue Nov 05 2019 Brian C. Lane <bcl@redhat.com> 32.2-1
- New lorax documentation - 32.2 (bcl@redhat.com)
- tests: Add 'test_mkksiso' tests (bcl@redhat.com)
- mkksiso: Add documentation (bcl@redhat.com)
- mkksiso: Add a tool to add a kickstart to an existing boot.iso (bcl@redhat.com)
- tests: Add a lorax boot.iso test (bcl@redhat.com)
- test: Add wait_boot method for root logins (bcl@redhat.com)
- tests: Ensure failure if beakerlib results file not found (atodorov@redhat.com)
- tests: Documentation updates (atodorov@redhat.com)
- tests: Use host repositories for make vm (atodorov@redhat.com)
- Remove unused make targets (atodorov@redhat.com)
- DRY when setting up, running & parsing results for beakerlib tests (atodorov@redhat.com)
- tests: Disable mirrors (atodorov@redhat.com)
- tests: Use journalctl -g to check for failed login (bcl@redhat.com)
- tests: Fix check_root_account when used with tar liveimg test (bcl@redhat.com)
- tests: Use the same asserts as before (atodorov@redhat.com)
- tests: switch to using podman instead of docker (atodorov@redhat.com)
- tests: Remove nested vm from tar liveimg kickstart test (bcl@redhat.com)
- tests: Use --http0.9 for curl ssh test (bcl@redhat.com)
- test: Boot the live-iso faster, and login using ssh key (bcl@redhat.com)
- test: Split up the test class to allow booting other images (bcl@redhat.com)
- tests: Split testing the image into a separate script (bcl@redhat.com)
- Add live iso support to s390 (bcl@redhat.com)
- docs: Override macboot/nomacboot documentation (bcl@redhat.com)
- Disable some compose types on other architectures (bcl@redhat.com)
- lorax: Drop unused --title option (bcl@redhat.com)
- tests: Document Azure setup (atodorov@redhat.com)
- tests: unskip Azure scenario (atodorov@redhat.com)

* Wed Oct 16 2019 Brian C. Lane <bcl@redhat.com> 32.1-1
- Bump default platform and releasever to 32 (bcl@redhat.com)
- New lorax documentation - 32.1 (bcl@redhat.com)
- docs: Fix Sphinx errors in docstrings (bcl@redhat.com)
- vm.install: Turn on verbose output (bcl@redhat.com)
- tests: Switch the azure examples used in the lifted tests to use aws (bcl@redhat.com)
- Remove lifted azure support (bcl@redhat.com)
- composer-cli: Add providers info <PROVIDER> command (bcl@redhat.com)
- composer-cli: Fix error handling in providers push (bcl@redhat.com)
- composer-cli: Fix upload log output (bcl@redhat.com)
- Add list to bash completion for composer-cli upload (bcl@redhat.com)
- Update composer-cli documentation (bcl@redhat.com)
- Add composer and lifted to coverage report (bcl@redhat.com)
- composer-cli: Add starting an upload to compose start (bcl@redhat.com)
- composer-cli: Add providers template command (bcl@redhat.com)
- bash_completion: Add support for new composer-cli commands (bcl@redhat.com)
- composer-cli: Add support for providers command (bcl@redhat.com)
- composer-cli: Add support for upload command (bcl@redhat.com)
- Increase ansible verbosity to 2 (bcl@redhat.com)
- lifted: Add support for AWS upload (bcl@redhat.com)
- lifted: Improve logging for upload playbooks (bcl@redhat.com)
- Add upload status examples to compose route docstrings (bcl@redhat.com)
- tests: Add tests for deleting unknown upload and profile (bcl@redhat.com)
- Add docstrings to the new upload functions in pylorax.api.queue (bcl@redhat.com)
- Change /compose/uploads/delete to /upload/delete (bcl@redhat.com)
- tests: Add test for /compose/uploads/delete (bcl@redhat.com)
- tests: Add tests for /compose/uploads/schedule (bcl@redhat.com)
- Add profile support to /uploads/schedule/ (bcl@redhat.com)
- tests: Fix comments about V1 API results including uploads data (bcl@redhat.com)
- lifted: Make sure inputs cannot have path elements (bcl@redhat.com)
- Use consistent naming for upload uuids (bcl@redhat.com)
- tests: Add tests for new upload routes (bcl@redhat.com)
- Fix some docstrings in the v1 API (bcl@redhat.com)
- lifted: Make sure providers list is always sorted (bcl@redhat.com)
- Add /upload/providers/delete route (bcl@redhat.com)
- lifted: Add delete_profile function and tests (bcl@redhat.com)
- Add support for starting a compose upload with the profile (bcl@redhat.com)
- lifted: Add a function to load the settings for a provider's profile (bcl@redhat.com)
- Fix pylint errors in lifted.upload (bcl@redhat.com)
- tests: Add yamllint of the lifted playbooks (bcl@redhat.com)
- tests: Add tests for the new lifted module (bcl@redhat.com)
- All providers should have 'supported_types' (bcl@redhat.com)
- lifted directories should be under share_dir and lib_dir (bcl@redhat.com)
- tests: Add tests for API v1 (bcl@redhat.com)
- Make sure V0 API doesn't return uploads information (bcl@redhat.com)
- Automatically upload composed images to the cloud (egoode@redhat.com)
- Add load and dump to pylorax.api.toml (egoode@redhat.com)
- Support CI testing against a bots project PR (martin@piware.de)
- Makefile: Don't clobber an existing bots checkout (martin@piware.de)
- lorax-composer: Handle RecipeError in commit_recipe_directory (bcl@redhat.com)
- test: Disable pylint subprocess check check (bcl@redhat.com)

* Mon Sep 30 2019 Brian C. Lane <bcl@redhat.com> 32.0-1
- aarch64: Fix live-iso creation on aarch64 (bcl@redhat.com)
- Add test for running composer with --no-system-repos option (jikortus@redhat.com)
- [tests] Use functions for starting and stopping lorax-composer (jikortus@redhat.com)
- Makefile: Update bots target for moved GitHub project (sanne.raymaekers@gmail.com)
- Keep the zramctl utility from util-linux on boot.iso (mkolman@redhat.com)
- Skip kickstart tar test for fedora-30/tar scenario (atodorov@redhat.com)
- Enable fedora-30/tar test scenario (atodorov@redhat.com)
- [tests] Collect compose logs after each build (atodorov@redhat.com)
- [tests] Use a function to wait for compose to finish (jikortus@redhat.com)
- When launching AWS instances wait for the one we just launched (atodorov@redhat.com)
- tests: Add kickstart tar installation test (jikortus@redhat.com)
- tests: add option to disable kernel command line parameters check (jikortus@redhat.com)
- tests: Use a loop to wait for VM and sshd to start (bcl@redhat.com)
- creator.py: include dmsquash-live-ntfs by default (gmt@be-evil.net)
- Skip Azure test b/c misconfigured infra & creds (atodorov@redhat.com)
- tests: Drop tito from the Dockerfile.test (bcl@redhat.com)
- tests: Drop sort from compose types test (bcl@redhat.com)
- Revert "tests: Fix the order of liveimg-tar live-iso" (atodorov@redhat.com)
- New test: assert toml files in git workspace (atodorov@redhat.com)

* Tue Aug 20 2019 Brian C. Lane <bcl@redhat.com> 31.10-1
- tests: Update gpg key to fedora 32 (bcl@redhat.com)
- tests: Fix the order of liveimg-tar live-iso (bcl@redhat.com)
- tests: Use server-2.repo instead of single.repo (bcl@redhat.com)
- lorax-composer: Add support for dnf variables to repo sources (bcl@redhat.com)
- Use smarter multipath detection logic. (dlehman@redhat.com)
- tests: Expand test coverage of the v0 and v1 sources API (bcl@redhat.com)
- tests: Temporarily work around rpm and pylint issues (bcl@redhat.com)
- lorax-composer: Add v1 API for projects/source/ (bcl@redhat.com)
- Add /api/v1/ handler with no routes (bcl@redhat.com)
- Move common functions into pylorax.api.utils (bcl@redhat.com)
- Document the release process steps (bcl@redhat.com)
- lorax-composer: Add liveimg-tar image type (bcl@redhat.com)
- livemedia-creator: Use --compress-arg in mksquashfs (bcl@redhat.com)
- livemedia-creator: Remove unused --squashfs_args option (bcl@redhat.com)
- Only use repos with valid urls for test_server.py (bcl@redhat.com)
- lorax-composer: Clarify groups documentation (bcl@redhat.com)

* Mon Jul 29 2019 Brian C. Lane <bcl@redhat.com> 31.9-1
- New lorax documentation - 31.9 (bcl@redhat.com)
- Remove .build-id from install media (riehecky@fnal.gov)
- lorax-composer: Add squashfs_only False to all image types (bcl@redhat.com)
- tests: Update test_creator.py (bcl@redhat.com)
- docs: Add anaconda-live to fedora-livemedia.ks example (bcl@redhat.com)
- livemedia-creator: Use make_runtime for all runtime creation (bcl@redhat.com)
- livemedia-creator: Add support for a squashfs only runtime image (bcl@redhat.com)
- Update rst formatting. Refs #815 (atodorov@redhat.com)
- don't skip Xorg packages on s390x to allow local GUI installation under KVM (dan@danny.cz)
- Use binary mode to tail the file (bcl@redhat.com)
- Return most relevant log file from /compose/log (egoode@redhat.com)
- Use passwd --status for locked root account check (jikortus@redhat.com)
- tests: Use liveuser account for live-iso boot check (bcl@redhat.com)
- Mention python3-magic in HACKING.md (egoode@redhat.com)
- tests: Add check to make sure the compose actually finished (bcl@redhat.com)
- test: check the number of tests that ran (atodorov@redhat.com)
- lorax: Add debug log of command line options (riehecky@fnal.gov)
- lorax: provide runtime lorax config in debug log (riehecky@fnal.gov)
- Remove whitespace in v0_blueprints_new (jacobdkozol@gmail.com)
- Add test for VALID_BLUEPRINT_NAME check (jacobdkozol@gmail.com)
- Add seperate validation for blueprint names (jacobdkozol@gmail.com)
- Leave lscpu in the image for additional debugging (riehecky@fnal.gov)
- tests: set skip_if_unavailable in test repos (lars@karlitski.net)
- test/README.md: Add section explaining GitHub integration (lars@karlitski.net)

* Fri Jun 28 2019 Brian C. Lane <bcl@redhat.com> 31.8-1
- Also search for pxeboot kernel and initrd pairs (hadess@hadess.net)
- Assert that RuntimeErrors have correct messages (egoode@redhat.com)
- More descriptive error for a bad ref in repos.git (egoode@redhat.com)
- Remove unused shell script (atodorov@redhat.com)
- test: Output results for cockpit's log.html (lars@karlitski.net)
- Do not generate journal.xml from beakerlib (atodorov@redhat.com)
- tests: Add RUN_TESTS to Makefile so you can pass in targets (bcl@redhat.com)
- tests: Add tests for recipe checking functions (bcl@redhat.com)
- lorax-composer: Add basic case check to check_recipe_dict (bcl@redhat.com)
- lorax-composer: Add basic recipe checker function (bcl@redhat.com)
- Revert "test: Disable test_live_iso test" (lars@karlitski.net)
- test: Fix test_blueprint_sanity (lars@karlitski.net)
- tests: rpm now returns str, drop decode() call (bcl@redhat.com)
- tests: Drop libgit2 install from koji (bcl@redhat.com)

* Tue Jun 18 2019 Brian C. Lane <bcl@redhat.com> 31.7-1
- New lorax documentation - 31.7 (bcl@redhat.com)
- Update qemu arguments to work correctly with nographic (bcl@redhat.com)
- Switch to new toml library (bcl@redhat.com)
- composer-cli: Update diff support for customizations and repos.git (bcl@redhat.com)
- Add support for customizations and repos.git to /blueprints/diff/ (bcl@redhat.com)
- tests: Update custom-base with customizations (bcl@redhat.com)
- Move the v0 API documentation into the functions (bcl@redhat.com)
- Update the /api/v0/ route handling to use the flask_blueprints Blueprint class (bcl@redhat.com)
- Extend Flask Blueprint class to allow skipping routes (bcl@redhat.com)
- Remove PR template (atodorov@redhat.com)
- Increase retry count/sleep times when waiting for lorax to start (atodorov@redhat.com)
- Revert "remove the check for qemu-kvm" (atodorov@redhat.com)
- Revert "remove the check for /usr/bin/docker in the setup phase" (atodorov@redhat.com)
- [tests] Define unbound variables in test scripts (atodorov@redhat.com)
- [tests] Handle blueprints in setup_tests/teardown_tests correctly (atodorov@redhat.com)
- [tests] grep|cut for IP address in a more robust way (atodorov@redhat.com)
- Remove quotes around file test in make vm (atodorov@redhat.com)
- test: Don't wait on --sit when test succeeds (lars@karlitski.net)
- Monkey-patch beakerlib to fail on first assert (lars@karlitski.net)
- test_cli.sh: Return beakerlib's exit code (lars@karlitski.net)
- Don't send CORS headers (lars@karlitski.net)
- tests: Set BLUEPRINTS_DIR in all cases (lars@karlitski.net)
- tests: Fail on script errors (lars@karlitski.net)
- Add API integration test (lars@karlitski.net)
- composer: Set up a custom HTTP error handler (lars@karlitski.net)
- Split live-iso and qcow2 and update test scenario execution (atodorov@redhat.com)
- Configure $PACKAGE for beakerlib reports (atodorov@redhat.com)
- Use cloud credentials during test if they exist (atodorov@redhat.com)
- Don't execute compose/blueprint sanity tests in Travis CI (atodorov@redhat.com)
- test: Add --list option to test/check* scripts (lars@karlitski.net)
- test: Add --sit argument to check-* scripts (lars@karlitski.net)
- test: Custom main() function (lars@karlitski.net)
- Use ansible instead of awscli (jstodola@redhat.com)
- Fix path to generic.prm (jstodola@redhat.com)
- Update example fedora-livemedia.ks (bcl@redhat.com)
- Update composer live-iso template (bcl@redhat.com)
- test: Disable test_live_iso test (lars@karlitski.net)
- tests: Source lib.sh from the right directory (lars@karlitski.net)
- Revert "Add rpmfluff temporarily" (bcl@redhat.com)
- tests: Update tmux version to 2.9a (bcl@redhat.com)
- test: Install beakerlib on non-RHEL images (martin@piware.de)
- tests: Fail immediately when image build fails (lars@karlitski.net)
- test: Install beakerlib wehn running on rhel (lars@karlitski.net)
- test: Generalize fs resizing in vm.install (lars@karlitski.net)
- tests: Re-enable kvm (lars@karlitski.net)
- test: Fix vm.install to be idempotent (lars@karlitski.net)
- tests: Don't depend on kvm for tar and qcow2 tests (lars@karlitski.net)
- test_compose_tar: Work around selinux policy change (lars@karlitski.net)
- test_compose_tar: Be less verbose (lars@karlitski.net)
- test_compose_tar: Fix docker test (lars@karlitski.net)
- tests: Extract images to /var/tmp, not /tmp (lars@karlitski.net)
- Use Cockpit's test images and infrastructure (lars@karlitski.net)
- pylint: Remove unused false positive (lars@karlitski.net)

* Thu May 16 2019 Brian C. Lane <bcl@redhat.com> 31.6-1
- Add kernel to ext4-filesystem template (bcl@redhat.com)
- Create a lorax-docs package with the html docs (bcl@redhat.com)
- Add new documentation branches to index.rst (bcl@redhat.com)

* Tue May 07 2019 Brian C. Lane <bcl@redhat.com> 31.5-1
- Add python3-pycdlib to Dockerfile.test (bcl@redhat.com)
- Replace isoinfo with pycdlib (bcl@redhat.com)
- Add test for passing custom option on kernel command line (jikortus@redhat.com)
- Use verify_image function as a helper for generic tests (jikortus@redhat.com)

* Thu May 02 2019 Brian C. Lane <bcl@redhat.com> 31.4-1
- tests: Update openssh-server to v8.* (bcl@redhat.com)
- New lorax documentation - 31.4 (bcl@redhat.com)
- Change customizations.firewall to append items instead of replace (bcl@redhat.com)
- Update customizations.services documentation (bcl@redhat.com)
- lorax-composer: Add services support to blueprints (bcl@redhat.com)
- Add rpmfluff temporarily (bcl@redhat.com)
- lorax-composer: Add firewall support to blueprints (bcl@redhat.com)
- lorax-composer: Add locale support to blueprints (bcl@redhat.com)
- lorax-composer: Fix customizations when creating a recipe (bcl@redhat.com)
- Update docs for new timezone section (bcl@redhat.com)
- lorax-composer: Add timezone support to blueprint (bcl@redhat.com)
- Proposal for adding to the blueprint customizations (bcl@redhat.com)
- Add test for starting compose with deleted blueprint (jikortus@redhat.com)
- Update VMware info for VMware testing (chrobert@redhat.com)
- tests: Cleanup on failure of in_tempdir (bcl@redhat.com)
- Change [[modules]] to [[packages]] in tests (atodorov@redhat.com)
- Add new test to verify compose paths exist (atodorov@redhat.com)
- Add new sanity tests for blueprints (atodorov@redhat.com)
- Fixes for locked root account test (jikortus@redhat.com)

* Fri Apr 05 2019 Brian C. Lane <bcl@redhat.com> 31.3-1
- Add -iso-level 3 when the install.img is > 4GiB (bcl@redhat.com)
- Correct "recipes" use to "blueprints" in composer-cli description (kwalker@redhat.com)
- Fix keeping files on Amazon s3 (jstodola@redhat.com)
- Allow to keep objects in AWS (jstodola@redhat.com)
- Fix the google cloud boot console settings (dshea@redhat.com)
- Add a compose type for alibaba. (dshea@redhat.com)
- Add a new compose type for Hyper-V (dshea@redhat.com)
- Add a compose check for google cloud images. (dshea@redhat.com)
- Add a compose type for Google Compute Engine (dshea@redhat.com)
- Add a new output type, tar-disk. (dshea@redhat.com)
- Support compressing single files. (dshea@redhat.com)
- Add an option to align the image size to a multiplier. (dshea@redhat.com)

* Mon Apr 01 2019 Brian C. Lane <bcl@redhat.com> 31.2-1
- Add documentation references to lorax-composer service files (bcl@redhat.com)
- Add more tests for gitrpm.py (bcl@redhat.com)
- lorax-composer: Fix installing files from [[repos.git]] to / (bcl@redhat.com)
- New lorax documentation - 31.1 (bcl@redhat.com)
- Make it easier to generate docs for the next release (bcl@redhat.com)

* Tue Mar 26 2019 Brian C. Lane <bcl@redhat.com> 31.1-1
- qemu wasn't restoring the terminal if it was terminated early (bcl@redhat.com)
- Switch the --virt-uefi method to use SecureBoot (bcl@redhat.com)
- pylorax.ltmpl: Add a test for missing quotes (bcl@redhat.com)
- Don't remove chmem and lsmem from install.img (bcl@redhat.com)
- lorax-composer: pass customization.kernel append to extra_boot_args (bcl@redhat.com)
- Improve logging for template syntax errors (bcl@redhat.com)
- Add extra boot args to the livemedia-creator iso templates (bcl@redhat.com)
- lorax-composer: Add the ability to append to the kernel command-line (bcl@redhat.com)
- Add checks for disabled root account (jikortus@redhat.com)
- Update datastore for VMware testing (chrobert@redhat.com)

* Fri Mar 15 2019 Brian C. Lane <bcl@redhat.com> 31.0-1
- Add tests using repos.git in blueprints (bcl@redhat.com)
- Move git repo creation into tests/lib.py (bcl@redhat.com)
- rpmgit: catch potential errors while running git (bcl@redhat.com)
- tests: Add test for Recipe.freeze() function (bcl@redhat.com)
- Add repos.git support to lorax-composer builds (bcl@redhat.com)
- Add pylorax.api.gitrpm module and tests (bcl@redhat.com)
- Add support for [[repos.git]] section to blueprints (bcl@redhat.com)
- Update ppc64le isolabel to match x86_64 logic (bcl@redhat.com)
- Add blacklist_exceptions to multipath.conf (bcl@redhat.com)
- tests: Add python3-mock and python3-sphinx_rtd_theme (bcl@redhat.com)
- Use make ci inside test-in-copy target (atodorov@redhat.com)
- Allow overriding $CLI outside test scripts (atodorov@redhat.com)
- tests: Make it easier to update version globs (bcl@redhat.com)
- New test: Build live-iso and boot with KVM (atodorov@redhat.com)
- lorax-composer: Return UnknownBlueprint errors when using deleted blueprints (bcl@redhat.com)
- lorax-composer: Delete workspace copy when deleting blueprint (bcl@redhat.com)
- New test: Build qcow2 compose and test it with QEMU-KVM (atodorov@redhat.com)
