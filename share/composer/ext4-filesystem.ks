# Lorax Composer filesystem output kickstart template

# Firewall configuration
firewall --enabled

# Root password
rootpw --plaintext removethispw
# Network information
network  --bootproto=dhcp --onboot=on --activate
# System authorization information
auth --useshadow --enablemd5
# System keyboard
keyboard --xlayouts=us --vckeymap=us
# System language
lang en_US.UTF-8
# SELinux configuration
selinux --enforcing
# Installation logging level
logging --level=info
# Shutdown after installation
shutdown
# System timezone
timezone  US/Eastern
# System bootloader configuration
bootloader --location=none
# Partition clearing information
clearpart --all --initlabel

%post
# Remove random-seed
rm /var/lib/systemd/random-seed
%end

# NOTE Do NOT add any other sections after %packages
%packages --nocore
# Packages requires to support this output format go here
policycoreutils

# NOTE lorax-composer will add the recipe packages below here, including the final %end
