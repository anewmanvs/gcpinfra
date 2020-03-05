"""
Configuration module for access in Google Cloud Platform

Sets JSON file for google environment variable.

Singleton
"""

# pylint: disable=invalid-name, too-few-public-methods

import os
import re
import json
import pathlib
from warnings import warn

from google.auth import default
from google.auth.transport.urllib3 import AuthorizedHttp

def valid_var_env():
    """Checks if var env GOOGLE_APPLICATION_CREDENTIALS is correctly set."""

    return ('GOOGLE_APPLICATION_CREDENTIALS' in os.environ
            and os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

class GCPConf:
    """Singleton configuration class."""

    __instance = None

    class __GCPConf:
        """Internal class."""

        def __init__(self, path, verbose):
            """Construtor da classe interna."""

            self.__valid = False
            self.verbose = verbose
            self.parent = str(pathlib.Path(__file__).parent.parent.absolute())
            self.tempdir = '/tmp'
            self.path = path

            if not self.path and not valid_var_env():
                raise ValueError("GCPConf is singleton and the first instance must "
                                 "pass a valid 'path' to a JSON containing access "
                                 "keys to your service account.\nFallback to env "
                                 "variable GOOGLE_APPLICATION_CREDENTIALS did not "
                                 "work.")
            elif valid_var_env():
                self.path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                warn("Param. 'path' invalid. Fallback using env var "
                     "GOOGLE_APPLICATION_CREDENTIALS.")

            if not os.path.exists(self.path):
                raise ValueError("No JSON found in '{}'. "
                                 "Please create a 'GCPConf' object"
                                 " with a valid path".format(self.path))
            else:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.path
                self.__valid = True

            self.__print('Instantiating new GCPConf in {}'.format(self.path))

            # set credentials
            self.scopes = ['https://www.googleapis.com/auth/cloud-platform']
            self.credentials, self.project_id = default(scopes=self.scopes)
            self.std_region = 'southamerica-east1'
            # call this only after std_region
            self.std_zone_uri = self.__get_std_zone()
            self.std_zone = self.get_zone_name(self.std_zone_uri)
            # if both are None inform a standard
            if self.std_zone is None:
                self.std_zone = 'southamerica-east1-a'
            if self.std_zone_uri is None:
                self.std_zone_uri = ('https://www.googleapis.com/compute/v1/'
                                     'projects/gm-mateus-estat/zones/southamerica'
                                     '-east1-a')

        def __print(self, msg):
            """Prints message if verbose is set."""

            if self.verbose:
                print(msg)

        def __bool__(self):
            """Returns true if path is valid."""

            return self.__valid

        @staticmethod
        def remove(filename):
            """Removes a file."""

            return os.remove(filename)

        def request(self, method, url, fields=None, headers=None):
            """Make a request using urllib3 AuthorizedHttp."""

            authed_http = AuthorizedHttp(self.credentials)
            return authed_http.request(method, url, fields=fields, headers=headers)

        def get(self, url, fields=None, headers=None):
            """Make a GET request using urllib3 AuthorizedHttp."""

            return self.request('GET', url, fields=fields, headers=headers)

        def __get_std_zone(self):
            """
            This method must be called after self.std_region and self.project_id
            are set.
            """

            url = 'https://compute.googleapis.com/compute/v1/projects/{}/regions/{}'

            try:
                response = self.get(url.format(self.project_id, self.std_region))
                data = json.loads(response.data)

                if response.status == 200:
                    if not data['zones']:
                        self.__print('No zone available for region {}'.format(
                            self.std_region))
                        return None

                    return data['zones'][0]  # returns the first zone
                else:  # something wrong happened
                    warn('Configuration works but is limited: {}'.format(
                        data['error']['message']))
                    return None
            except Exception as excp:
                self.__print('Failed to retrieve region information: {}'.format(
                    excp))
                return None

        @staticmethod
        def get_zone_name(std_zone_uri):
            """Get zone name by zone URI."""

            if std_zone_uri is None:
                return None

            match = re.match('.+/zones/(.+)', std_zone_uri)
            return match.group(1)  # if this fails, the URI has changed

    def __init__(self, path=None, verbose=False):
        """Construtor singleton."""

        if not GCPConf.__instance:
            GCPConf.__instance = GCPConf.__GCPConf(path, verbose)
        elif verbose:
            print('Using same GCPConf in {}'.format(GCPConf.__instance.path))

    def __getattr__(self, attr):
        """Aponta atributos não existentes para os atributos da classe interna."""

        # se a class interna também não tiver, vai lançar uma exceção de atributo
        return getattr(self.__instance, attr)
