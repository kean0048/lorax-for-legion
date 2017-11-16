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
import logging
log = logging.getLogger("lorax-composer")

from flask import jsonify, request

# Use pykickstart to calculate disk image size
from pykickstart.parser import KickstartParser
from pykickstart.version import makeVersion, RHEL7

from pylorax.api.crossdomain import crossdomain
from pylorax.api.recipes import list_branch_files, read_recipe_commit, recipe_filename, list_commits
from pylorax.api.recipes import recipe_from_dict, recipe_from_toml, commit_recipe, delete_recipe, revert_recipe
from pylorax.api.recipes import tag_recipe_commit, recipe_diff
from pylorax.api.workspace import workspace_read, workspace_write, workspace_delete
from pylorax.creator import DRACUT_DEFAULT, mount_boot_part_over_root
from pylorax.creator import make_appliance, make_image, make_livecd, make_live_images
from pylorax.creator import make_runtime, make_squashfs
from pylorax.imgutils import copytree
from pylorax.imgutils import Mount, PartitionMount, umount
from pylorax.installer import InstallError
from pylorax.sysutils import joinpaths

# The API functions don't actually get called by any code here
# pylint: disable=unused-variable

# no-virt mode doesn't need libvirt, so make it optional
try:
    import libvirt
except ImportError:
    libvirt = None

def take_limits(iterable, offset, limit):
    return iterable[offset:][:limit]

def v0_api(api):
    """ Setup v0 of the API server"""
    @api.route("/api/v0/status")
    @crossdomain(origin="*")
    def v0_status():
        return jsonify(build="devel", api="0", db_version="0", schema_version="0", db_supported=False)

    @api.route("/api/v0/recipes/list")
    @crossdomain(origin="*")
    def v0_recipes_list():
        """List the available recipes on a branch."""
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError as e:
            return jsonify(error={"msg":str(e)}), 400

        with api.config["GITLOCK"].lock:
            recipes = take_limits(map(lambda f: f[:-5], list_branch_files(api.config["GITLOCK"].repo, "master")), offset, limit)
        return jsonify(recipes=recipes, limit=limit, offset=offset, total=len(recipes))

    @api.route("/api/v0/recipes/info/<recipe_names>")
    @crossdomain(origin="*")
    def v0_recipes_info(recipe_names):
        """Return the contents of the recipe, or a list of recipes"""
        recipes = []
        changes = []
        errors = []
        for recipe_name in [n.strip() for n in recipe_names.split(",")]:
            exceptions = []
            # Get the workspace version (if it exists)
            try:
                with api.config["GITLOCK"].lock:
                    ws_recipe = workspace_read(api.config["GITLOCK"].repo, "master", recipe_name)
            except Exception as e:
                ws_recipe = None
                exceptions.append(str(e))
                log.error("(v0_recipes_info) %s", str(e))

            # Get the git version (if it exists)
            try:
                with api.config["GITLOCK"].lock:
                    git_recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name)
            except Exception as e:
                git_recipe = None
                exceptions.append(str(e))
                log.error("(v0_recipes_info) %s", str(e))

            if not ws_recipe and not git_recipe:
                # Neither recipe, return an error
                errors.append({"recipe":recipe_name, "msg":", ".join(exceptions)})
            elif ws_recipe and not git_recipe:
                # No git recipe, return the workspace recipe
                changes.append({"name":recipe_name, "changed":True})
                recipes.append(ws_recipe)
            elif not ws_recipe and git_recipe:
                # No workspace recipe, no change, return the git recipe
                changes.append({"name":recipe_name, "changed":False})
                recipes.append(git_recipe)
            else:
                # Both exist, maybe changed, return the workspace recipe
                changes.append({"name":recipe_name, "changed":ws_recipe != git_recipe})
                recipes.append(ws_recipe)

        # Sort all the results by case-insensitive recipe name
        changes = sorted(changes, key=lambda c: c["name"].lower())
        recipes = sorted(recipes, key=lambda r: r["name"].lower())
        errors = sorted(errors, key=lambda e: e["recipe"].lower())

        return jsonify(changes=changes, recipes=recipes, errors=errors)

    @api.route("/api/v0/recipes/changes/<recipe_names>")
    @crossdomain(origin="*")
    def v0_recipes_changes(recipe_names):
        """Return the changes to a recipe or list of recipes"""
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError as e:
            return jsonify(error={"msg":str(e)}), 400

        recipes = []
        errors = []
        for recipe_name in [n.strip() for n in recipe_names.split(",")]:
            filename = recipe_filename(recipe_name)
            try:
                with api.config["GITLOCK"].lock:
                    commits = take_limits(list_commits(api.config["GITLOCK"].repo, "master", filename), offset, limit)
            except Exception as e:
                errors.append({"recipe":recipe_name, "msg":e})
                log.error("(v0_recipes_changes) %s", str(e))
            else:
                recipes.append({"name":recipe_name, "changes":commits, "total":len(commits)})

        recipes = sorted(recipes, key=lambda r: r["name"].lower())
        errors = sorted(errors, key=lambda e: e["recipe"].lower())

        return jsonify(recipes=recipes, errors=errors, offset=offset, limit=limit)

    @api.route("/api/v0/recipes/new", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_new():
        """Commit a new recipe"""
        try:
            if request.headers['Content-Type'] == "text/x-toml":
                recipe = recipe_from_toml(request.data)
            else:
                recipe = recipe_from_dict(request.get_json(cache=False))

            with api.config["GITLOCK"].lock:
                commit_recipe(api.config["GITLOCK"].repo, "master", recipe)

                # Read the recipe with new version and write it to the workspace
                recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe["name"])
                workspace_write(api.config["GITLOCK"].repo, "master", recipe)
        except Exception as e:
            log.error("(v0_recipes_new) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/delete/<recipe_name>", methods=["DELETE"])
    @crossdomain(origin="*")
    def v0_recipes_delete(recipe_name):
        """Delete a recipe from git"""
        try:
            with api.config["GITLOCK"].lock:
                delete_recipe(api.config["GITLOCK"].repo, "master", recipe_name)
        except Exception as e:
            log.error("(v0_recipes_delete) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/workspace", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_workspace():
        """Write a recipe to the workspace"""
        try:
            if request.headers['Content-Type'] == "text/x-toml":
                recipe = recipe_from_toml(request.data)
            else:
                recipe = recipe_from_dict(request.get_json(cache=False))

            with api.config["GITLOCK"].lock:
                workspace_write(api.config["GITLOCK"].repo, "master", recipe)
        except Exception as e:
            log.error("(v0_recipes_workspace) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/workspace/<recipe_name>", methods=["DELETE"])
    @crossdomain(origin="*")
    def v0_recipes_delete_workspace(recipe_name):
        """Delete a recipe from the workspace"""
        try:
            with api.config["GITLOCK"].lock:
                workspace_delete(api.config["GITLOCK"].repo, "master", recipe_name)
        except Exception as e:
            log.error("(v0_recipes_delete_workspace) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/undo/<recipe_name>/<commit>", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_undo(recipe_name, commit):
        """Undo changes to a recipe by reverting to a previous commit."""
        try:
            with api.config["GITLOCK"].lock:
                revert_recipe(api.config["GITLOCK"].repo, "master", recipe_name, commit)

                # Read the new recipe and write it to the workspace
                recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name)
                workspace_write(api.config["GITLOCK"].repo, "master", recipe)
        except Exception as e:
            log.error("(v0_recipes_undo) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/tag/<recipe_name>", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_tag(recipe_name):
        """Tag a recipe's latest recipe commit as a 'revision'"""
        try:
            with api.config["GITLOCK"].lock:
                tag_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name)
        except Exception as e:
            log.error("(v0_recipes_tag) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/diff/<recipe_name>/<from_commit>/<to_commit>")
    @crossdomain(origin="*")
    def v0_recipes_diff(recipe_name, from_commit, to_commit):
        """Return the differences between two commits of a recipe"""
        try:
            if from_commit == "NEWEST":
                with api.config["GITLOCK"].lock:
                    old_recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name)
            else:
                with api.config["GITLOCK"].lock:
                    old_recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name, from_commit)
        except Exception as e:
            log.error("(v0_recipes_diff) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400

        try:
            if to_commit == "WORKSPACE":
                with api.config["GITLOCK"].lock:
                    new_recipe = workspace_read(api.config["GITLOCK"].repo, "master", recipe_name)
            elif to_commit == "NEWEST":
                with api.config["GITLOCK"].lock:
                    new_recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name)
            else:
                with api.config["GITLOCK"].lock:
                    new_recipe = read_recipe_commit(api.config["GITLOCK"].repo, "master", recipe_name, to_commit)
        except Exception as e:
            log.error("(v0_recipes_diff) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400

        diff = recipe_diff(old_recipe, new_recipe)
        return jsonify(diff=diff)
