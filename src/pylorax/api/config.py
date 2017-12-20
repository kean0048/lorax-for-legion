#
# Copyright (C) 2017  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import ConfigParser
import os

from pylorax.sysutils import joinpaths

class ComposerConfig(ConfigParser.SafeConfigParser):
    def get_default(self, section, option, default):
        try:
            return self.get(section, option)
        except ConfigParser.Error:
            return default


def configure(conf_file="/etc/lorax/composer.conf", root_dir="/", test_config=False):
    """lorax-composer configuration

    :param conf_file: Path to the config file overriding the default settings
    :type conf_file: str
    :param root_dir: Directory to prepend to paths, defaults to /
    :type root_dir: str
    :param test_config: Set to True to skip reading conf_file
    :type test_config: bool
    """
    conf = ComposerConfig()

    # set defaults
    conf.add_section("composer")
    conf.set("composer", "yum_conf", joinpaths(root_dir, "/var/lib/lorax/composer/yum.conf"))
    conf.set("composer", "repo_dir", joinpaths(root_dir, "/var/lib/lorax/composer/repos.d/"))
    conf.set("composer", "cache_dir", joinpaths(root_dir, "/var/cache/lorax/composer/yum/"))

    # Enable user authentication
    conf.set("composer", "auth", "1")

    # Only root is allowed to use composer
    conf.add_section("users")
    conf.set("users", "root", "1")

    # Enable all available repo files by default
    conf.add_section("repos")
    conf.set("repos", "use_system_repos", "1")
    conf.set("repos", "enabled", "*")

    if not test_config:
        # read the config file
        if os.path.isfile(conf_file):
            conf.read(conf_file)

    # Create any missing directories
    for section, key in [("composer", "yum_conf"), ("composer", "repo_dir"), ("composer", "cache_dir")]:
        path = conf.get(section, key)
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

    return conf
