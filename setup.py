from distutils.core import setup, Command

import datetime
import os
import sys



CURDIR = os.getcwd()
sys.path.append(CURDIR)



PACKAGE = "depgraph"

## For daily snapshots:
#VERSION = "0.0.1" + datetime.datetime.now().strftime("%Y%m%d")
VERSION = "0.0.1"

DESCRIPTION = "RPM dependency resolver"




class SrpmCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('sdist')
        self.build_rpm()

    def build_rpm(self):
        params = dict()

        topdir = params["topdir"] = os.path.abspath(CURDIR)
        rpmdir = params["rpmdir"] = os.path.join(topdir, "dist")
        rpmspec = params["rpmspec"] = os.path.join(topdir, "%s.spec" % PACKAGE)

        for subdir in ("RPMS", "BUILD", "BUILDROOT"):
            sdir = params[subdir] = os.path.join(rpmdir, subdir)

            if not os.path.exists(sdir):
                os.makedirs(sdir, 0755)

        open(rpmspec, "w").write(open(rpmspec + ".in").read().replace("@VERSION@", VERSION))

        cmd = """rpmbuild -bs \
            --define \"_topdir %(rpmdir)s\" --define \"_rpmdir %(rpmdir)s\" \
            --define \"_sourcedir %(topdir)s/dist\" --define \"_buildroot %(BUILDROOT)s\" \
            %(rpmspec)s
            """ % params

        os.system(cmd)



class RpmCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('sdist')
        self.build_rpm()

    def build_rpm(self):
        params = dict()

        topdir = params["topdir"] = os.path.abspath(CURDIR)
        rpmdir = params["rpmdir"] = os.path.join(topdir, "dist")
        rpmspec = params["rpmspec"] = os.path.join(topdir, "%s.spec" % PACKAGE)

        for subdir in ("RPMS", "BUILD", "BUILDROOT"):
            sdir = params[subdir] = os.path.join(rpmdir, subdir)

            if not os.path.exists(sdir):
                os.makedirs(sdir, 0755)

        open(rpmspec, "w").write(open(rpmspec + ".in").read().replace("@VERSION@", VERSION))

        cmd = """rpmbuild -bb \
            --define \"_topdir %(rpmdir)s\" --define \"_srcrpmdir %(rpmdir)s\" \
            --define \"_sourcedir %(topdir)s/dist\" --define \"_buildroot %(BUILDROOT)s\" \
            %(rpmspec)s
            """ % params

        os.system(cmd)



setup(name=PACKAGE,
    version=VERSION,
    description=DESCRIPTION,
    author="Ken SUGAWARA",
    author_email="ksugawar@redhat.com",
    license="GPLv3+",
    url="https://github.com/sugaken-r3/depgraph",
    packages=[
        "depgraph",
    ],
    scripts=[
        "depgraph.py",
    ],
    cmdclass={
        "srpm": SrpmCommand,
        "rpm":  RpmCommand,
    },
)

# vim:sw=4 ts=4 et:
