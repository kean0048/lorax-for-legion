#
# Copyright (C) 2017-2018  Red Hat, Inc.
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
""" Setup v0 of the API server

v0_api() must be called to setup the API routes for Flask

Status Responses
----------------

Some requests only return a status/error response.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

  Example response::

      {
        "status": true
      }

  Error response::

      {
        "error": {
          "msg": "ggit-error: Failed to remove entry. File isn't in the tree - jboss.toml (-1)"
        },
        "status": false
      }

API Routes
----------

All of the recipes routes support the optional `branch` argument. If it is not
used then the API will use the `master` branch for recipes. If you want to create
a new branch use the `new` or `workspace` routes with ?branch=<branch-name> to
store the new recipe on the new branch.

`/api/v0/test`
^^^^^^^^^^^^^^

  Return a test string. It is not JSON encoded.

`/api/v0/status`
^^^^^^^^^^^^^^^^
  Return the status of the API Server::

      { "api": "0",
        "build": "devel",
        "db_supported": false,
        "db_version": "0",
        "schema_version": "0" }

`/api/v0/recipes/list`
^^^^^^^^^^^^^^^^^^^^^^

  List the available recipes::

      { "limit": 20,
        "offset": 0,
        "recipes": [
          "atlas",
          "development",
          "glusterfs",
          "http-server",
          "jboss",
          "kubernetes" ],
        "total": 6 }

`/api/v0/recipes/info/<recipe_names>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the JSON representation of the recipe. This includes 3 top level
  objects.  `changes` which lists whether or not the workspace is different from
  the most recent commit. `recipes` which lists the JSON representation of the
  recipe, and `errors` which will list any errors, like non-existant recipes.

  Example::

      {
        "changes": [
          {
            "changed": false,
            "name": "glusterfs"
          }
        ],
        "errors": [],
        "recipes": [
          {
            "description": "An example GlusterFS server with samba",
            "modules": [
              {
                "name": "glusterfs",
                "version": "3.7.*"
              },
              {
                "name": "glusterfs-cli",
                "version": "3.7.*"
              }
            ],
            "name": "glusterfs",
            "packages": [
              {
                "name": "2ping",
                "version": "3.2.1"
              },
              {
                "name": "samba",
                "version": "4.2.*"
              }
            ],
            "version": "0.0.6"
          }
        ]
      }

  Error example::

      {
        "changes": [],
        "errors": [
          {
            "msg": "ggit-error: the path 'missing.toml' does not exist in the given tree (-3)",
            "recipe": "missing"
          }
        ],
        "recipes": []
      }

`/api/v0/recipes/changes/<recipe_names>[?offset=0&limit=20]`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the commits to a recipe. By default it returns the first 20 commits, this
  can be changed by passing `offset` and/or `limit`. The response will include the
  commit hash, summary, timestamp, and optionally the revision number. The commit
  hash can be passed to `/api/v0/recipes/diff/` to retrieve the exact changes.

  Example::

      {
        "errors": [],
        "limit": 20,
        "offset": 0,
        "recipes": [
          {
            "changes": [
              {
                "commit": "e083921a7ed1cf2eec91ad12b9ad1e70ef3470be",
                "message": "Recipe glusterfs, version 0.0.6 saved.",
                "revision": null,
                "timestamp": "2017-11-23T00:18:13Z"
              },
              {
                "commit": "cee5f4c20fc33ea4d54bfecf56f4ad41ad15f4f3",
                "message": "Recipe glusterfs, version 0.0.5 saved.",
                "revision": null,
                "timestamp": "2017-11-11T01:00:28Z"
              },
              {
                "commit": "29b492f26ed35d80800b536623bafc51e2f0eff2",
                "message": "Recipe glusterfs, version 0.0.4 saved.",
                "revision": null,
                "timestamp": "2017-11-11T00:28:30Z"
              },
              {
                "commit": "03374adbf080fe34f5c6c29f2e49cc2b86958bf2",
                "message": "Recipe glusterfs, version 0.0.3 saved.",
                "revision": null,
                "timestamp": "2017-11-10T23:15:52Z"
              },
              {
                "commit": "0e08ecbb708675bfabc82952599a1712a843779d",
                "message": "Recipe glusterfs, version 0.0.2 saved.",
                "revision": null,
                "timestamp": "2017-11-10T23:14:56Z"
              },
              {
                "commit": "3e11eb87a63d289662cba4b1804a0947a6843379",
                "message": "Recipe glusterfs, version 0.0.1 saved.",
                "revision": null,
                "timestamp": "2017-11-08T00:02:47Z"
              }
            ],
            "name": "glusterfs",
            "total": 6
          }
        ]
      }

POST `/api/v0/recipes/new`
^^^^^^^^^^^^^^^^^^^^^^^^^^

  Create a new recipe, or update an existing recipe. This supports both JSON and TOML
  for the recipe format. The recipe should be in the body of the request with the
  `Content-Type` header set to either `application/json` or `text/x-toml`.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

DELETE `/api/v0/recipes/delete/<recipe_name>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Delete a recipe. The recipe is deleted from the branch, and will no longer
  be listed by the `list` route. A recipe can be undeleted using the `undo` route
  to revert to a previous commit.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

POST `/api/v0/recipes/workspace`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Write a recipe to the temporary workspace. This works exactly the same as `new` except
  that it does not create a commit. JSON and TOML bodies are supported.

  The workspace is meant to be used as a temporary recipe storage for clients.
  It will be read by the `info` and `diff` routes if it is different from the
  most recent commit.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

DELETE `/api/v0/recipes/workspace/<recipe_name>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Remove the temporary workspace copy of a recipe. The `info` route will now
  return the most recent commit of the recipe. Any changes that were in the
  workspace will be lost.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

POST `/api/v0/recipes/undo/<recipe_name>/<commit>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  This will revert the recipe to a previous commit. The commit hash from the `changes`
  route can be used in this request.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

POST `/api/v0/recipes/tag/<recipe_name>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Tag a recipe as a new release. This uses git tags with a special format.
  `refs/tags/<branch>/<filename>/r<revision>`. Only the most recent recipe commit
  can be tagged. Revisions start at 1 and increment for each new tag
  (per-recipe). If the commit has already been tagged it will return false.

  The response will be a status response with `status` set to true, or an
  error response with it set to false and an error message included.

`/api/v0/recipes/diff/<recipe_name>/<from_commit>/<to_commit>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the differences between two commits, or the workspace. The commit hash
  from the `changes` response can be used here, or several special strings:

  - NEWEST will select the newest git commit. This works for `from_commit` or `to_commit`
  - WORKSPACE will select the workspace copy. This can only be used in `to_commit`

  eg. `/api/v0/recipes/diff/glusterfs/NEWEST/WORKSPACE` will return the differences
  between the most recent git commit and the contents of the workspace.

  Each entry in the response's diff object contains the old recipe value and the new one.
  If old is null and new is set, then it was added.
  If new is null and old is set, then it was removed.
  If both are set, then it was changed.

  The old/new entries will have the name of the recipe field that was changed. This
  can be one of: Name, Description, Version, Module, or Package.
  The contents for these will be the old/new values for them.

  In the example below the version was changed and the ping package was added.

  Example::

      {
        "diff": [
          {
            "new": {
              "Version": "0.0.6"
            },
            "old": {
              "Version": "0.0.5"
            }
          },
          {
            "new": {
              "Package": {
                "name": "ping",
                "version": "3.2.1"
              }
            },
            "old": null
          }
        ]
      }

`/api/v0/recipes/freeze/<recipe_names>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return a JSON representation of the recipe with the package and module versions set
  to the exact versions chosen by depsolving the recipe.

  Example::

      {
        "errors": [],
        "recipes": [
          {
            "recipe": {
              "description": "An example GlusterFS server with samba",
              "modules": [
                {
                  "name": "glusterfs",
                  "version": "3.8.4-18.4.el7.x86_64"
                },
                {
                  "name": "glusterfs-cli",
                  "version": "3.8.4-18.4.el7.x86_64"
                }
              ],
              "name": "glusterfs",
              "packages": [
                {
                  "name": "ping",
                  "version": "2:3.2.1-2.el7.noarch"
                },
                {
                  "name": "samba",
                  "version": "4.6.2-8.el7.x86_64"
                }
              ],
              "version": "0.0.6"
            }
          }
        ]
      }

`/api/v0/recipes/depsolve/<recipe_names>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Depsolve the recipe using yum, return the recipe used, and the NEVRAs of the packages
  chosen to satisfy the recipe's requirements. The response will include a list of results,
  with the full dependency list in `dependencies`, the NEVRAs for the recipe's direct modules
  and packages in `modules`, and any error will be in `errors`.

  Example::

      {
        "errors": [],
        "recipes": [
          {
            "dependencies": [
              {
                "arch": "noarch",
                "epoch": "0",
                "name": "2ping",
                "release": "2.el7",
                "version": "3.2.1"
              },
              {
                "arch": "x86_64",
                "epoch": "0",
                "name": "acl",
                "release": "12.el7",
                "version": "2.2.51"
              },
              {
                "arch": "x86_64",
                "epoch": "0",
                "name": "audit-libs",
                "release": "3.el7",
                "version": "2.7.6"
              },
              {
                "arch": "x86_64",
                "epoch": "0",
                "name": "avahi-libs",
                "release": "17.el7",
                "version": "0.6.31"
              },
              ...
            ],
            "modules": [
              {
                "arch": "noarch",
                "epoch": "0",
                "name": "2ping",
                "release": "2.el7",
                "version": "3.2.1"
              },
              {
                "arch": "x86_64",
                "epoch": "0",
                "name": "glusterfs",
                "release": "18.4.el7",
                "version": "3.8.4"
              },
              ...
            ],
            "recipe": {
              "description": "An example GlusterFS server with samba",
              "modules": [
                {
                  "name": "glusterfs",
                  "version": "3.7.*"
                },
             ...
            }
          }
        ]
      }

`/api/v0/projects/list[?offset=0&limit=20]`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  List all of the available projects. By default this returns the first 20 items,
  but this can be changed by setting the `offset` and `limit` arguments.

  Example::

      {
        "limit": 20,
        "offset": 0,
        "projects": [
          {
            "description": "0 A.D. (pronounced \"zero ey-dee\") is a ...",
            "homepage": "http://play0ad.com",
            "name": "0ad",
            "summary": "Cross-Platform RTS Game of Ancient Warfare",
            "upstream_vcs": "UPSTREAM_VCS"
          },
          ...
        ],
        "total": 21770
      }

`/api/v0/projects/info/<project_names>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return information about the comma-separated list of projects. It includes the description
  of the package along with the list of available builds.

  Example::

      {
        "projects": [
          {
            "builds": [
              {
                "arch": "x86_64",
                "build_config_ref": "BUILD_CONFIG_REF",
                "build_env_ref": "BUILD_ENV_REF",
                "build_time": "2017-03-01T08:39:23",
                "changelog": "- restore incremental backups correctly, files ...",
                "epoch": "2",
                "metadata": {},
                "release": "32.el7",
                "source": {
                  "license": "GPLv3+",
                  "metadata": {},
                  "source_ref": "SOURCE_REF",
                  "version": "1.26"
                }
              }
            ],
            "description": "The GNU tar program saves many ...",
            "homepage": "http://www.gnu.org/software/tar/",
            "name": "tar",
            "summary": "A GNU file archiving program",
            "upstream_vcs": "UPSTREAM_VCS"
          }
        ]
      }

`/api/v0/projects/depsolve/<project_names>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Depsolve the comma-separated list of projects and return the list of NEVRAs needed
  to satisfy the request.

  Example::

      {
        "projects": [
          {
            "arch": "noarch",
            "epoch": "0",
            "name": "basesystem",
            "release": "7.el7",
            "version": "10.0"
          },
          {
            "arch": "x86_64",
            "epoch": "0",
            "name": "bash",
            "release": "28.el7",
            "version": "4.2.46"
          },
          {
            "arch": "x86_64",
            "epoch": "0",
            "name": "filesystem",
            "release": "21.el7",
            "version": "3.2"
          },
          ...
        ]
      }

`/api/v0/modules/list[?offset=0&limit=20]`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return a list of all of the available modules. This includes the name and the
  group_type, which is always "rpm" for lorax-composer. By default this returns
  the first 20 items. This can be changed by setting the `offset` and `limit`
  arguments.

  Example::

      {
        "limit": 20,
        "modules": [
          {
            "group_type": "rpm",
            "name": "0ad"
          },
          {
            "group_type": "rpm",
            "name": "0ad-data"
          },
          {
            "group_type": "rpm",
            "name": "0install"
          },
          {
            "group_type": "rpm",
            "name": "2048-cli"
          },
          ...
        ]
        "total": 21770
      }

`/api/v0/modules/list/<module_names>[?offset=0&limit=20]`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the list of comma-separated modules. Output is the same as `/modules/list`

  Example::

      {
        "limit": 20,
        "modules": [
          {
            "group_type": "rpm",
            "name": "tar"
          }
        ],
        "offset": 0,
        "total": 1
      }

`/api/v0/modules/info/<module_names>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the module's dependencies, and the information about the module.

  Example::

      {
        "modules": [
          {
            "dependencies": [
              {
                "arch": "noarch",
                "epoch": "0",
                "name": "basesystem",
                "release": "7.el7",
                "version": "10.0"
              },
              {
                "arch": "x86_64",
                "epoch": "0",
                "name": "bash",
                "release": "28.el7",
                "version": "4.2.46"
              },
              ...
            ],
            "description": "The GNU tar program saves ...",
            "homepage": "http://www.gnu.org/software/tar/",
            "name": "tar",
            "summary": "A GNU file archiving program",
            "upstream_vcs": "UPSTREAM_VCS"
          }
        ]
      }

POST `/api/v0/compose`
^^^^^^^^^^^^^^^^^^^^^^

  Start a compose. The content type should be 'application/json' and the body of the POST
  should look like this::

      {
        "recipe_name": "http-server",
        "compose_type": "tar",
        "branch": "master"
      }

  Pass it the name of the recipe, the type of output (from '/api/v0/compose/types'), and the
  recipe branch to use. 'branch' is optional and will default to master. It will create a new
  build and add it to the queue. It returns the build uuid and a status if it succeeds::

      {
        "build_id": "e6fa6db4-9c81-4b70-870f-a697ca405cdf",
        "status": true
      }

`/api/v0/compose/types`
^^^^^^^^^^^^^^^^^^^^^^^

  Returns the list of supported output types that are valid for use with 'POST /api/v0/compose'

      {
        "types": [
          {
            "enabled": true,
            "name": "tar"
          }
        ]
      }

`/api/v0/compose/queue`
^^^^^^^^^^^^^^^^^^^^^^^

  Return the status of the build queue. It includes information about the builds waiting,
  and the build that is running.

  Example::

      {
        "new": [
          {
            "id": "45502a6d-06e8-48a5-a215-2b4174b3614b",
            "recipe": "glusterfs",
            "queue_status": "WAITING",
            "timestamp": 1517362647.4570868,
            "version": "0.0.6"
          },
          {
            "id": "6d292bd0-bec7-4825-8d7d-41ef9c3e4b73",
            "recipe": "kubernetes",
            "queue_status": "WAITING",
            "timestamp": 1517362659.0034983,
            "version": "0.0.1"
          }
        ],
        "run": [
          {
            "id": "745712b2-96db-44c0-8014-fe925c35e795",
            "recipe": "glusterfs",
            "queue_status": "RUNNING",
            "timestamp": 1517362633.7965999,
            "version": "0.0.6"
          }
        ]
      }

`/api/v0/compose/finished`
^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the details on all of the finished composes on the system.

  Example::

      {
        "finished": [
          {
            "id": "70b84195-9817-4b8a-af92-45e380f39894",
            "recipe": "glusterfs",
            "queue_status": "FINISHED",
            "timestamp": 1517351003.8210032,
            "version": "0.0.6"
          },
          {
            "id": "e695affd-397f-4af9-9022-add2636e7459",
            "recipe": "glusterfs",
            "queue_status": "FINISHED",
            "timestamp": 1517362289.7193348,
            "version": "0.0.6"
          }
        ]
      }

`/api/v0/compose/failed`
^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the details on all of the failed composes on the system.

  Example::

      {
        "failed": [
           {
            "id": "8c8435ef-d6bd-4c68-9bf1-a2ef832e6b1a",
            "recipe": "http-server",
            "queue_status": "FAILED",
            "timestamp": 1517523249.9301329,
            "version": "0.0.2"
          }
        ]
      }

`/api/v0/compose/status/<uuids>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Return the details for each of the comma-separated list of uuids.

  Example::

      {
        "uuids": [
          {
            "id": "8c8435ef-d6bd-4c68-9bf1-a2ef832e6b1a",
            "recipe": "http-server",
            "queue_status": "FINISHED",
            "timestamp": 1517523644.2384307,
            "version": "0.0.2"
          },
          {
            "id": "45502a6d-06e8-48a5-a215-2b4174b3614b",
            "recipe": "glusterfs",
            "queue_status": "FINISHED",
            "timestamp": 1517363442.188399,
            "version": "0.0.6"
          }
        ]
      }

DELETE `/api/v0/recipes/cancel/<uuid>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Cancel the build, if it is not finished, and delete the results. It will return a
  status of True if it is successful.

  Example::

      {
        "status": true,
        "uuid": "03397f8d-acff-4cdb-bd31-f629b7a948f5"
      }

DELETE `/api/v0/compose/delete/<uuids>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Delete the list of comma-separated uuids from the compose results.

  Example::

      {
        "errors": [],
        "uuids": [
          {
            "status": true,
            "uuid": "ae1bf7e3-7f16-4c9f-b36e-3726a1093fd0"
          }
        ]
      }

`/api/v0/compose/info/<uuid>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Get detailed information about the compose. The returned JSON string will
  contain the following information:

    * id - The uuid of the comoposition
    * config - containing the configuration settings used to run Anaconda
    * recipe - The depsolved recipe used to generate the kickstart
    * commit - The (local) git commit hash for the recipe used
    * deps - The NEVRA of all of the dependencies used in the composition
    * compose_type - The type of output generated (tar, iso, etc.)
    * queue_status - The final status of the composition (FINISHED or FAILED)

  Example::

      {
        "commit": "7078e521a54b12eae31c3fd028680da7a0815a4d",
        "compose_type": "tar",
        "config": {
          "anaconda_args": "",
          "armplatform": "",
          "compress_args": [],
          "compression": "xz",
          "image_name": "root.tar.xz",
          ...
        },
        "deps": {
          "packages": [
            {
              "arch": "x86_64",
              "epoch": "0",
              "name": "acl",
              "release": "14.el7",
              "version": "2.2.51"
            }
          ]
        },
        "id": "c30b7d80-523b-4a23-ad52-61b799739ce8",
        "queue_status": "FINISHED",
        "recipe": {
          "description": "An example kubernetes master",
          ...
        }
      }

`/api/v0/compose/metadata/<uuid>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Returns a .tar of the metadata used for the build. This includes all the
  information needed to reproduce the build, including the final kickstart
  populated with repository and package NEVRA.

  The mime type is set to 'application/x-tar' and the filename is set to
  UUID-metadata.tar

  The .tar is uncompressed, but is not large.

`/api/v0/compose/results/<uuid>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Returns a .tar of the metadata, logs, and output image of the build. This
  includes all the information needed to reproduce the build, including the
  final kickstart populated with repository and package NEVRA. The output image
  is already in compressed form so the returned tar is not compressed.

  The mime type is set to 'application/x-tar' and the filename is set to
  UUID.tar

`/api/v0/compose/logs/<uuid>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Returns a .tar of the anaconda build logs. The tar is not compressed, but is
  not large.

  The mime type is set to 'application/x-tar' and the filename is set to
  UUID-logs.tar

`/api/v0/compose/image/<uuid>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Returns the output image from the build. The filename is set to the filename
  from the build. eg. root.tar.xz or boot.iso.

`/api/v0/compose/log/<uuid>[?size=kbytes]`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  Returns the end of the anaconda.log. The size parameter is optional and defaults to 1Mbytes
  if it is not included. The returned data is raw text from the end of the logfile, starting on
  a line boundry.

  Example::

      12:59:24,222 INFO anaconda: Running Thread: AnaConfigurationThread (140629395244800)
      12:59:24,223 INFO anaconda: Configuring installed system
      12:59:24,912 INFO anaconda: Configuring installed system
      12:59:24,912 INFO anaconda: Creating users
      12:59:24,913 INFO anaconda: Clearing libuser.conf at /tmp/libuser.Dyy8Gj
      12:59:25,154 INFO anaconda: Creating users
      12:59:25,155 INFO anaconda: Configuring addons
      12:59:25,155 INFO anaconda: Configuring addons
      12:59:25,155 INFO anaconda: Generating initramfs
      12:59:49,467 INFO anaconda: Generating initramfs
      12:59:49,467 INFO anaconda: Running post-installation scripts
      12:59:49,467 INFO anaconda: Running kickstart %%post script(s)
      12:59:50,782 INFO anaconda: All kickstart %%post script(s) have been run
      12:59:50,782 INFO anaconda: Running post-installation scripts
      12:59:50,784 INFO anaconda: Thread Done: AnaConfigurationThread (140629395244800)

"""

import logging
log = logging.getLogger("lorax-composer")

from flask import jsonify, request, Response, send_file

from pylorax.api.compose import start_build, compose_types
from pylorax.api.crossdomain import crossdomain
from pylorax.api.projects import projects_list, projects_info, projects_depsolve
from pylorax.api.projects import modules_list, modules_info, ProjectsError
from pylorax.api.queue import queue_status, build_status, uuid_delete, uuid_status, uuid_info
from pylorax.api.queue import uuid_tar, uuid_image, uuid_cancel, uuid_log
from pylorax.api.recipes import list_branch_files, read_recipe_commit, recipe_filename, list_commits
from pylorax.api.recipes import recipe_from_dict, recipe_from_toml, commit_recipe, delete_recipe, revert_recipe
from pylorax.api.recipes import tag_recipe_commit, recipe_diff
from pylorax.api.workspace import workspace_read, workspace_write, workspace_delete

# The API functions don't actually get called by any code here
# pylint: disable=unused-variable

def take_limits(iterable, offset, limit):
    """ Apply offset and limit to an iterable object

    :param iterable: The object to limit
    :type iterable: iter
    :param offset: The number of items to skip
    :type offset: int
    :param limit: The total number of items to return
    :type limit: int
    :returns: A subset of the iterable
    """
    return iterable[offset:][:limit]

def v0_api(api):
    # Note that Sphinx will not generate documentations for any of these.
    @api.route("/api/v0/test")
    @crossdomain(origin="*")
    def v0_test():
        return "API v0 test"

    @api.route("/api/v0/status")
    @crossdomain(origin="*")
    def v0_status():
        return jsonify(build="devel", api="0", db_version="0", schema_version="0", db_supported=False)

    @api.route("/api/v0/recipes/list")
    @crossdomain(origin="*")
    def v0_recipes_list():
        """List the available recipes on a branch."""
        branch = request.args.get("branch", "master")
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError as e:
            return jsonify(error={"msg":str(e)}), 400

        with api.config["GITLOCK"].lock:
            recipes = take_limits(map(lambda f: f[:-5], list_branch_files(api.config["GITLOCK"].repo, branch)), offset, limit)
        return jsonify(recipes=recipes, limit=limit, offset=offset, total=len(recipes))

    @api.route("/api/v0/recipes/info/<recipe_names>")
    @crossdomain(origin="*")
    def v0_recipes_info(recipe_names):
        """Return the contents of the recipe, or a list of recipes"""
        branch = request.args.get("branch", "master")
        recipes = []
        changes = []
        errors = []
        for recipe_name in [n.strip() for n in recipe_names.split(",")]:
            exceptions = []
            # Get the workspace version (if it exists)
            try:
                with api.config["GITLOCK"].lock:
                    ws_recipe = workspace_read(api.config["GITLOCK"].repo, branch, recipe_name)
            except Exception as e:
                ws_recipe = None
                exceptions.append(str(e))
                log.error("(v0_recipes_info) %s", str(e))

            # Get the git version (if it exists)
            try:
                with api.config["GITLOCK"].lock:
                    git_recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
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
        branch = request.args.get("branch", "master")
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
                    commits = take_limits(list_commits(api.config["GITLOCK"].repo, branch, filename), offset, limit)
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
        branch = request.args.get("branch", "master")
        try:
            if request.headers['Content-Type'] == "text/x-toml":
                recipe = recipe_from_toml(request.data)
            else:
                recipe = recipe_from_dict(request.get_json(cache=False))

            with api.config["GITLOCK"].lock:
                commit_recipe(api.config["GITLOCK"].repo, branch, recipe)

                # Read the recipe with new version and write it to the workspace
                recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe["name"])
                workspace_write(api.config["GITLOCK"].repo, branch, recipe)
        except Exception as e:
            log.error("(v0_recipes_new) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/delete/<recipe_name>", methods=["DELETE"])
    @crossdomain(origin="*")
    def v0_recipes_delete(recipe_name):
        """Delete a recipe from git"""
        branch = request.args.get("branch", "master")
        try:
            with api.config["GITLOCK"].lock:
                delete_recipe(api.config["GITLOCK"].repo, branch, recipe_name)
        except Exception as e:
            log.error("(v0_recipes_delete) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/workspace", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_workspace():
        """Write a recipe to the workspace"""
        branch = request.args.get("branch", "master")
        try:
            if request.headers['Content-Type'] == "text/x-toml":
                recipe = recipe_from_toml(request.data)
            else:
                recipe = recipe_from_dict(request.get_json(cache=False))

            with api.config["GITLOCK"].lock:
                workspace_write(api.config["GITLOCK"].repo, branch, recipe)
        except Exception as e:
            log.error("(v0_recipes_workspace) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/workspace/<recipe_name>", methods=["DELETE"])
    @crossdomain(origin="*")
    def v0_recipes_delete_workspace(recipe_name):
        """Delete a recipe from the workspace"""
        branch = request.args.get("branch", "master")
        try:
            with api.config["GITLOCK"].lock:
                workspace_delete(api.config["GITLOCK"].repo, branch, recipe_name)
        except Exception as e:
            log.error("(v0_recipes_delete_workspace) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/undo/<recipe_name>/<commit>", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_undo(recipe_name, commit):
        """Undo changes to a recipe by reverting to a previous commit."""
        branch = request.args.get("branch", "master")
        try:
            with api.config["GITLOCK"].lock:
                revert_recipe(api.config["GITLOCK"].repo, branch, recipe_name, commit)

                # Read the new recipe and write it to the workspace
                recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
                workspace_write(api.config["GITLOCK"].repo, branch, recipe)
        except Exception as e:
            log.error("(v0_recipes_undo) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/tag/<recipe_name>", methods=["POST"])
    @crossdomain(origin="*")
    def v0_recipes_tag(recipe_name):
        """Tag a recipe's latest recipe commit as a 'revision'"""
        branch = request.args.get("branch", "master")
        try:
            with api.config["GITLOCK"].lock:
                tag_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
        except Exception as e:
            log.error("(v0_recipes_tag) %s", str(e))
            return jsonify(status=False, error={"msg":str(e)}), 400
        else:
            return jsonify(status=True)

    @api.route("/api/v0/recipes/diff/<recipe_name>/<from_commit>/<to_commit>")
    @crossdomain(origin="*")
    def v0_recipes_diff(recipe_name, from_commit, to_commit):
        """Return the differences between two commits of a recipe"""
        branch = request.args.get("branch", "master")
        try:
            if from_commit == "NEWEST":
                with api.config["GITLOCK"].lock:
                    old_recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
            else:
                with api.config["GITLOCK"].lock:
                    old_recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name, from_commit)
        except Exception as e:
            log.error("(v0_recipes_diff) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        try:
            if to_commit == "WORKSPACE":
                with api.config["GITLOCK"].lock:
                    new_recipe = workspace_read(api.config["GITLOCK"].repo, branch, recipe_name)
            elif to_commit == "NEWEST":
                with api.config["GITLOCK"].lock:
                    new_recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
            else:
                with api.config["GITLOCK"].lock:
                    new_recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name, to_commit)
        except Exception as e:
            log.error("(v0_recipes_diff) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        diff = recipe_diff(old_recipe, new_recipe)
        return jsonify(diff=diff)

    @api.route("/api/v0/recipes/freeze/<recipe_names>")
    @crossdomain(origin="*")
    def v0_recipes_freeze(recipe_names):
        """Return the recipe with the exact modules and packages selected by depsolve"""
        branch = request.args.get("branch", "master")
        recipes = []
        errors = []
        for recipe_name in [n.strip() for n in sorted(recipe_names.split(","), key=lambda n: n.lower())]:
            # get the recipe
            # Get the workspace version (if it exists)
            recipe = None
            try:
                with api.config["GITLOCK"].lock:
                    recipe = workspace_read(api.config["GITLOCK"].repo, branch, recipe_name)
            except Exception:
                pass

            if not recipe:
                # No workspace version, get the git version (if it exists)
                try:
                    with api.config["GITLOCK"].lock:
                        recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
                except Exception as e:
                    errors.append({"recipe":recipe_name, "msg":str(e)})
                    log.error("(v0_recipes_freeze) %s", str(e))

            # No recipe found, skip it.
            if not recipe:
                errors.append({"recipe":recipe_name, "msg":"Recipe not found"})
                continue

            # Combine modules and packages and depsolve the list
            # TODO include the version/glob in the depsolving
            module_names = recipe.module_names
            package_names = recipe.package_names
            projects = sorted(set(module_names+package_names), key=lambda n: n.lower())
            deps = []
            try:
                with api.config["YUMLOCK"].lock:
                    deps = projects_depsolve(api.config["YUMLOCK"].yb, projects)
            except ProjectsError as e:
                errors.append({"recipe":recipe_name, "msg":str(e)})
                log.error("(v0_recipes_freeze) %s", str(e))

            recipes.append({"recipe": recipe.freeze(deps)})

        return jsonify(recipes=recipes, errors=errors)

    @api.route("/api/v0/recipes/depsolve/<recipe_names>")
    @crossdomain(origin="*")
    def v0_recipes_depsolve(recipe_names):
        """Return the dependencies for a recipe"""
        branch = request.args.get("branch", "master")
        recipes = []
        errors = []
        for recipe_name in [n.strip() for n in sorted(recipe_names.split(","), key=lambda n: n.lower())]:
            # get the recipe
            # Get the workspace version (if it exists)
            recipe = None
            try:
                with api.config["GITLOCK"].lock:
                    recipe = workspace_read(api.config["GITLOCK"].repo, branch, recipe_name)
            except Exception:
                pass

            if not recipe:
                # No workspace version, get the git version (if it exists)
                try:
                    with api.config["GITLOCK"].lock:
                        recipe = read_recipe_commit(api.config["GITLOCK"].repo, branch, recipe_name)
                except Exception as e:
                    errors.append({"recipe":recipe_name, "msg":str(e)})
                    log.error("(v0_recipes_depsolve) %s", str(e))

            # No recipe found, skip it.
            if not recipe:
                errors.append({"recipe":recipe_name, "msg":"Recipe not found"})
                continue

            # Combine modules and packages and depsolve the list
            # TODO include the version/glob in the depsolving
            module_names = map(lambda m: m["name"], recipe["modules"] or [])
            package_names = map(lambda p: p["name"], recipe["packages"] or [])
            projects = sorted(set(module_names+package_names), key=lambda n: n.lower())
            deps = []
            try:
                with api.config["YUMLOCK"].lock:
                    deps = projects_depsolve(api.config["YUMLOCK"].yb, projects)
            except ProjectsError as e:
                errors.append({"recipe":recipe_name, "msg":str(e)})
                log.error("(v0_recipes_depsolve) %s", str(e))

            # Get the NEVRA's of the modules and projects, add as "modules"
            modules = []
            for dep in deps:
                if dep["name"] in projects:
                    modules.append(dep)
            modules = sorted(modules, key=lambda m: m["name"].lower())

            recipes.append({"recipe":recipe, "dependencies":deps, "modules":modules})

        return jsonify(recipes=recipes, errors=errors)

    @api.route("/api/v0/projects/list")
    @crossdomain(origin="*")
    def v0_projects_list():
        """List all of the available projects/packages"""
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError as e:
            return jsonify(error={"msg":str(e)}), 400

        try:
            with api.config["YUMLOCK"].lock:
                available = projects_list(api.config["YUMLOCK"].yb)
        except ProjectsError as e:
            log.error("(v0_projects_list) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        projects = take_limits(available, offset, limit)
        return jsonify(projects=projects, offset=offset, limit=limit, total=len(available))

    @api.route("/api/v0/projects/info/<project_names>")
    @crossdomain(origin="*")
    def v0_projects_info(project_names):
        """Return detailed information about the listed projects"""
        try:
            with api.config["YUMLOCK"].lock:
                projects = projects_info(api.config["YUMLOCK"].yb, project_names.split(","))
        except ProjectsError as e:
            log.error("(v0_projects_info) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        return jsonify(projects=projects)

    @api.route("/api/v0/projects/depsolve/<project_names>")
    @crossdomain(origin="*")
    def v0_projects_depsolve(project_names):
        """Return detailed information about the listed projects"""
        try:
            with api.config["YUMLOCK"].lock:
                deps = projects_depsolve(api.config["YUMLOCK"].yb, project_names.split(","))
        except ProjectsError as e:
            log.error("(v0_projects_depsolve) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        return jsonify(projects=deps)

    @api.route("/api/v0/modules/list")
    @api.route("/api/v0/modules/list/<module_names>")
    @crossdomain(origin="*")
    def v0_modules_list(module_names=None):
        """List available modules, filtering by module_names"""
        try:
            limit = int(request.args.get("limit", "20"))
            offset = int(request.args.get("offset", "0"))
        except ValueError as e:
            return jsonify(error={"msg":str(e)}), 400

        if module_names:
            module_names = module_names.split(",")

        try:
            with api.config["YUMLOCK"].lock:
                available = modules_list(api.config["YUMLOCK"].yb, module_names)
        except ProjectsError as e:
            log.error("(v0_modules_list) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        modules = take_limits(available, offset, limit)
        return jsonify(modules=modules, offset=offset, limit=limit, total=len(available))

    @api.route("/api/v0/modules/info/<module_names>")
    @crossdomain(origin="*")
    def v0_modules_info(module_names):
        """Return detailed information about the listed modules"""
        try:
            with api.config["YUMLOCK"].lock:
                modules = modules_info(api.config["YUMLOCK"].yb, module_names.split(","))
        except ProjectsError as e:
            log.error("(v0_modules_info) %s", str(e))
            return jsonify(error={"msg":str(e)}), 400

        return jsonify(modules=modules)

    @api.route("/api/v0/compose", methods=["POST"])
    @crossdomain(origin="*")
    def v0_compose_start():
        """Start a compose

        The body of the post should have these fields:
          recipe_name   - The recipe name from /recipes/list/
          compose_type  - The type of output to create, from /compose/types
          branch        - Optional, defaults to master, selects the git branch to use for the recipe.
        """
        # Passing ?test=1 will generate a fake FAILED compose.
        # Passing ?test=2 will generate a fake FINISHED compose.
        try:
            test_mode = int(request.args.get("test", "0"))
        except ValueError:
            test_mode = 0

        compose = request.get_json(cache=False)

        errors = []
        if not compose:
            return jsonify(status=False, error={"msg":"Missing POST body"}), 400

        if "recipe_name" not in compose:
            errors.append("No 'recipe_name' in the JSON request")
        else:
            recipe_name = compose["recipe_name"]

        if "branch" not in compose or not compose["branch"]:
            branch = "master"
        else:
            branch = compose["branch"]

        if "compose_type" not in compose:
            errors.append("No 'compose_type' in the JSON request")
        else:
            compose_type = compose["compose_type"]

        if errors:
            return jsonify(status=False, error={"msg":"\n".join(errors)}), 400

        try:
            build_id = start_build(api.config["COMPOSER_CFG"], api.config["YUMLOCK"], api.config["GITLOCK"],
                                   branch, recipe_name, compose_type, test_mode)
        except Exception as e:
            return jsonify(status=False, error={"msg":str(e)}), 400

        return jsonify(status=True, build_id=build_id)

    @api.route("/api/v0/compose/types")
    @crossdomain(origin="*")
    def v0_compose_types():
        """Return the list of enabled output types

        (only enabled types are returned)
        """
        share_dir = api.config["COMPOSER_CFG"].get("composer", "share_dir")
        return jsonify(types=[{"name": k, "enabled": True} for k in compose_types(share_dir)])

    @api.route("/api/v0/compose/queue")
    @crossdomain(origin="*")
    def v0_compose_queue():
        """Return the status of the new and running queues"""
        return jsonify(queue_status(api.config["COMPOSER_CFG"]))

    @api.route("/api/v0/compose/finished")
    @crossdomain(origin="*")
    def v0_compose_finished():
        """Return the list of finished composes"""
        return jsonify(finished=build_status(api.config["COMPOSER_CFG"], "FINISHED"))

    @api.route("/api/v0/compose/failed")
    @crossdomain(origin="*")
    def v0_compose_failed():
        """Return the list of failed composes"""
        return jsonify(failed=build_status(api.config["COMPOSER_CFG"], "FAILED"))

    @api.route("/api/v0/compose/status/<uuids>")
    @crossdomain(origin="*")
    def v0_compose_status(uuids):
        """Return the status of the listed uuids"""
        results = []
        for uuid in [n.strip().lower() for n in uuids.split(",")]:
            details = uuid_status(api.config["COMPOSER_CFG"], uuid)
            if details is not None:
                results.append(details)

        return jsonify(uuids=results)

    @api.route("/api/v0/compose/cancel/<uuid>", methods=["DELETE"])
    @crossdomain(origin="*")
    def v0_compose_cancel(uuid):
        """Cancel a running compose and delete its results directory"""
        status = uuid_status(api.config["COMPOSER_CFG"], uuid)
        if status is None:
            return jsonify(status=False, msg="%s is not a valid build uuid" % uuid), 400

        if status["queue_status"] not in ["WAITING", "RUNNING"]:
            return jsonify(status=False, uuid=uuid, msg="Cannot cancel a build that is in the %s state" % status["queue_status"])

        try:
            uuid_cancel(api.config["COMPOSER_CFG"], uuid)
        except Exception as e:
            return jsonify(status=False, uuid=uuid, msg=str(e))
        else:
            return jsonify(status=True, uuid=uuid)

    @api.route("/api/v0/compose/delete/<uuids>", methods=["DELETE"])
    @crossdomain(origin="*")
    def v0_compose_delete(uuids):
        """Delete the compose results for the listed uuids"""
        results = []
        errors = []
        for uuid in [n.strip().lower() for n in uuids.split(",")]:
            status = uuid_status(api.config["COMPOSER_CFG"], uuid)
            if status is None:
                errors.append({"uuid": uuid, "msg": "Not a valid build uuid"})
            elif status["queue_status"] not in ["FINISHED", "FAILED"]:
                errors.append({"uuid":uuid, "msg":"Build not in FINISHED or FAILED."})
            else:
                try:
                    uuid_delete(api.config["COMPOSER_CFG"], uuid)
                except Exception as e:
                    errors.append({"uuid":uuid, "msg":str(e)})
                else:
                    results.append({"uuid":uuid, "status":True})
        return jsonify(uuids=results, errors=errors)

    @api.route("/api/v0/compose/info/<uuid>")
    @crossdomain(origin="*")
    def v0_compose_info(uuid):
        """Return detailed info about a compose"""
        try:
            info = uuid_info(api.config["COMPOSER_CFG"], uuid)
        except Exception as e:
            return jsonify(status=False, msg=str(e))

        return jsonify(**info)

    @api.route("/api/v0/compose/metadata/<uuid>")
    @crossdomain(origin="*")
    def v0_compose_metadata(uuid):
        """Return a tar of the metadata for the build"""
        status = uuid_status(api.config["COMPOSER_CFG"], uuid)
        if status is None:
            return jsonify(status=False, msg="%s is not a valid build uuid" % uuid), 400
        if status["queue_status"] not in ["FINISHED", "FAILED"]:
            return jsonify(status=False, uuid=uuid, msg="Build not in FINISHED or FAILED.")
        else:
            return Response(uuid_tar(api.config["COMPOSER_CFG"], uuid, metadata=True, image=False, logs=False),
                            mimetype="application/x-tar",
                            headers=[("Content-Disposition", "attachment; filename=%s-metadata.tar;" % uuid)],
                            direct_passthrough=True)

    @api.route("/api/v0/compose/results/<uuid>")
    @crossdomain(origin="*")
    def v0_compose_results(uuid):
        """Return a tar of the metadata and the results for the build"""
        status = uuid_status(api.config["COMPOSER_CFG"], uuid)
        if status is None:
            return jsonify(status=False, msg="%s is not a valid build uuid" % uuid), 400
        elif status["queue_status"] not in ["FINISHED", "FAILED"]:
            return jsonify(status=False, uuid=uuid, msg="Build not in FINISHED or FAILED.")
        else:
            return Response(uuid_tar(api.config["COMPOSER_CFG"], uuid, metadata=True, image=True, logs=True),
                            mimetype="application/x-tar",
                            headers=[("Content-Disposition", "attachment; filename=%s.tar;" % uuid)],
                            direct_passthrough=True)

    @api.route("/api/v0/compose/logs/<uuid>")
    @crossdomain(origin="*")
    def v0_compose_logs(uuid):
        """Return a tar of the metadata for the build"""
        status = uuid_status(api.config["COMPOSER_CFG"], uuid)
        if status is None:
            return jsonify(status=False, msg="%s is not a valid build uuid"), 400
        elif status["queue_status"] not in ["FINISHED", "FAILED"]:
            return jsonify(status=False, uuid=uuid, msg="Build not in FINISHED or FAILED.")
        else:
            return Response(uuid_tar(api.config["COMPOSER_CFG"], uuid, metadata=False, image=False, logs=True),
                            mimetype="application/x-tar",
                            headers=[("Content-Disposition", "attachment; filename=%s-logs.tar;" % uuid)],
                            direct_passthrough=True)

    @api.route("/api/v0/compose/image/<uuid>")
    @crossdomain(origin="*")
    def v0_compose_image(uuid):
        """Return the output image for the build"""
        status = uuid_status(api.config["COMPOSER_CFG"], uuid)
        if status is None:
            return jsonify(status=False, msg="%s is not a valid build uuid" % uuid), 400
        elif status["queue_status"] not in ["FINISHED", "FAILED"]:
            return jsonify(status=False, uuid=uuid, msg="Build not in FINISHED or FAILED.")
        else:
            image_name, image_path = uuid_image(api.config["COMPOSER_CFG"], uuid)

            # XXX - Will mime type guessing work for all our output?
            return send_file(image_path, as_attachment=True, attachment_filename=image_name, add_etags=False)

    @api.route("/api/v0/compose/log/<uuid>")
    @crossdomain(origin="*")
    def v0_compose_log_tail(uuid):
        """Return the end of the main anaconda.log, defaults to 1Mbytes"""
        try:
            size = int(request.args.get("size", "1024"))
        except ValueError as e:
            return jsonify(error={"msg":str(e)}), 400

        status = uuid_status(api.config["COMPOSER_CFG"], uuid)
        if status is None or status["queue_status"] == "WAITING":
            return jsonify(status=False, uuid=uuid, msg="Build has not started yet. No logs to view")
        try:
            return Response(uuid_log(api.config["COMPOSER_CFG"], uuid, size), direct_passthrough=True)
        except RuntimeError as e:
            return jsonify(status=False, uuid=uuid, msg=str(e))
