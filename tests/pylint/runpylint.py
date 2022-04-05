#!/usr/bin/python3

import sys

from pocketlint import FalsePositive, PocketLintConfig, PocketLinter
import pylint

class LoraxLintConfig(PocketLintConfig):
    def __init__(self):
        PocketLintConfig.__init__(self)

        self.falsePositives = [ FalsePositive(r"Module 'pylorax' has no 'version' member"),
                                FalsePositive(r"Catching too general exception Exception"),
                                # See https://bugzilla.redhat.com/show_bug.cgi?id=1739167
                                FalsePositive(r"Module 'rpm' has no '.*' member"),
                                FalsePositive(r"raise-missing-from"),
                                FalsePositive(r"redundant-u-string-prefix"),
                                FalsePositive(r"unspecified-encoding"),
                              ]

    @property
    def pylintPlugins(self):
        retval = super(LoraxLintConfig, self).pylintPlugins
        # Not using threads so we can skip this
        retval.remove("pocketlint.checkers.environ")
        # No markup used
        retval.remove("pocketlint.checkers.markup")
        return retval

    @property
    def ignoreNames(self):
        return { "bots", "rpmbuild", "rel-eng" }

    @property
    def extraArgs(self):
        return ["--extension-pkg-whitelist=rpm"]

if __name__ == "__main__":
    print("INFO: Using pylint v%s" % pylint.__version__)
    conf = LoraxLintConfig()
    linter = PocketLinter(conf)
    rc = linter.run()
    sys.exit(rc)
