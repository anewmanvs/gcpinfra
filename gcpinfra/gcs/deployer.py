"""
Deploy module - deploys code files to bucket into specified dirs.
"""

# pylint: disable=invalid-name, too-many-arguments, too-many-instance-attributes
# pylint: disable=too-few-public-methods, anomalous-backslash-in-string

import re

from glob import glob

from gcpinfra.gcp.conf import GCPConf
from gcpinfra.gcs.comms import GCSComms

class GCSDeployer:
    """
    Deploys codes to a GCS dir, replacing the old ones.

    Does not delete files not listed in the local dir.
    Replaces matched files in the remote dir.

    Files that should be ignore must be informed in 'skip' parameter.
    """

    def __init__(self, bucketname, destinationdir, localdir, skip=None,
                 topleveldir=None, verbose=False):
        """Constructor."""

        self.verbose = verbose
        self.bucketname = bucketname
        self.destinationdir = self.__trailing_backslash(destinationdir)
        self.localdir = self.__trailing_backslash(localdir)
        self.topleveldir = self.__trailing_backslash(topleveldir)
        self.skip = skip

        if self.skip and not isinstance(skip, list):
            self.skip = [self.skip]
        elif not self.skip:
            self.skip = []

        self.__prepare_regex()
        self.files_deploy = self.__find_files()

        self.conf = GCPConf(verbose=verbose)
        self.comms = GCSComms(bucketname, verbose=verbose)

        self.__print('Using top level dir {}'.format(self.topleveldir))

    def __print(self, msg):
        """Prints message accordingly to 'verbose' param."""

        if self.verbose:
            print(msg)

    @staticmethod
    def __trailing_backslash(path):
        """Removes blackslash from variables that contains paths."""

        if not path:
            return path

        if path[-1] != '/':
            return path

        return path[:-1]

    def __prepare_regex(self):
        """Prepares patterns to match."""

        pttrns = []
        for rg in self.skip:
            rg = rg.replace('.', '\.').replace('*', '.*')
            pttrns.append(re.compile(rg))
            self.__print('Skipping pattern {}'.format(rg))

        self.skip = pttrns

    def __find_files(self):
        """Find files to deploy."""

        filepttn = re.compile('{}/(.*\.*)$'.format(self.topleveldir))
        res = []
        files = glob('{}/**/*.*'.format(self.localdir), recursive=True)
        for _file in files:
            _file = _file.replace('./', '')
            remove = False
            for skip_pttrn in self.skip:
                if skip_pttrn.match(_file):
                    remove = True
                    break
            if not remove:
                relativepath = filepttn.match(_file).group(1)
                res.append((_file, relativepath))
                self.__print('{} found'.format(_file))

        return res

    def deploy(self):
        """
        Deploys files to GCS destination.
        """

        self.__print('Starting deploy')
        for _file, relativepath in self.files_deploy:
            path = '{}/{}'.format(self.destinationdir, relativepath)
            self.comms.upload_file(_file, path, replacepolicy='replace')
