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
import tempfile
from threading import Lock
import unittest

from flask import json
from pylorax.api.recipes import open_or_create_repo, commit_recipe_directory
from pylorax.api.server import server, GitLock


class ServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        repo_dir = tempfile.mkdtemp(prefix="lorax.test.repo.")
        server.config["REPO_DIR"] = repo_dir
        repo = open_or_create_repo(server.config["REPO_DIR"])
        server.config["GITLOCK"] = GitLock(repo=repo, lock=Lock(), dir=repo_dir)

        server.config['TESTING'] = True
        self.server = server.test_client()

        # Import the example recipes
        commit_recipe_directory(server.config["GITLOCK"].repo, "master", "tests/pylorax/recipes/")

    @classmethod
    def tearDownClass(self):
        pass

    def test_status(self):
        """Test the /api/v0/status route"""
        status_dict = {"build":"devel", "api":"0", "db_version":"0", "schema_version":"0", "db_supported":False}
        resp = self.server.get("/api/v0/status")
        data = json.loads(resp.data)
        self.assertEqual(data, status_dict)

    def test_recipes_list(self):
        """Test the /api/v0/recipes/list route"""
        list_dict = {"recipes":["atlas", "development", "glusterfs", "http-server", "jboss", "kubernetes"],
                     "limit":20, "offset":0, "total":6}
        resp = self.server.get("/api/v0/recipes/list")
        data = json.loads(resp.data)
        self.assertEqual(data, list_dict)

    def test_recipes_info(self):
        """Test the /api/v0/recipes/info route"""
        info_dict_1 = {"changes":[{"changed":False, "name":"http-server"}],
                       "errors":[],
                       "recipes":[{"description":"An example http server with PHP and MySQL support.",
                                   "modules":[{"name":"httpd", "version":"2.4.*"},
                                              {"name":"mod_auth_kerb", "version":"5.4"},
                                              {"name":"mod_ssl", "version":"2.4.*"},
                                              {"name":"php", "version":"5.4.*"},
                                              {"name": "php-mysql", "version":"5.4.*"}],
                                   "name":"http-server",
                                   "packages": [{"name":"openssh-server", "version": "6.6.*"},
                                                {"name": "rsync", "version": "3.0.*"},
                                                {"name": "tmux", "version": "2.2"}],
                                   "version": "0.0.1"}]}
        resp = self.server.get("/api/v0/recipes/info/http-server")
        data = json.loads(resp.data)
        self.assertEqual(data, info_dict_1)

        info_dict_2 = {"changes":[{"changed":False, "name":"glusterfs"},
                                  {"changed":False, "name":"http-server"}],
                       "errors":[],
                       "recipes":[{"description": "An example GlusterFS server with samba",
                                   "modules":[{"name":"glusterfs", "version":"3.7.*"},
                                              {"name":"glusterfs-cli", "version":"3.7.*"}],
                                   "name":"glusterfs",
                                   "packages":[{"name":"samba", "version":"4.2.*"}],
                                   "version": "0.0.1"},
                                  {"description":"An example http server with PHP and MySQL support.",
                                   "modules":[{"name":"httpd", "version":"2.4.*"},
                                              {"name":"mod_auth_kerb", "version":"5.4"},
                                              {"name":"mod_ssl", "version":"2.4.*"},
                                              {"name":"php", "version":"5.4.*"},
                                              {"name": "php-mysql", "version":"5.4.*"}],
                                   "name":"http-server",
                                   "packages": [{"name":"openssh-server", "version": "6.6.*"},
                                                {"name": "rsync", "version": "3.0.*"},
                                                {"name": "tmux", "version": "2.2"}],
                                   "version": "0.0.1"},
                                 ]}
        resp = self.server.get("/api/v0/recipes/info/http-server,glusterfs")
        data = json.loads(resp.data)
        self.assertEqual(data, info_dict_2)

        info_dict_3 = {"changes":[],
                "errors":[{"recipe":"missing-recipe", "msg":"ggit-error: the path 'missing-recipe.toml' does not exist in the given tree (-3)"}],
                       "recipes":[]
                      }
        resp = self.server.get("/api/v0/recipes/info/missing-recipe")
        data = json.loads(resp.data)
        self.assertEqual(data, info_dict_3)

    def test_recipes_changes(self):
        """Test the /api/v0/recipes/changes route"""
        resp = self.server.get("/api/v0/recipes/changes/http-server")
        data = json.loads(resp.data)

        # Can't compare a whole dict since commit hash and timestamps will change.
        # Should have 1 commit (for now), with a matching message.
        self.assertEqual(data["limit"], 20)
        self.assertEqual(data["offset"], 0)
        self.assertEqual(len(data["errors"]), 0)
        self.assertEqual(len(data["recipes"]), 1)
        self.assertEqual(data["recipes"][0]["name"], "http-server")
        self.assertEqual(len(data["recipes"][0]["changes"]), 1)
