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

from google.auth import default
from google.auth.transport.urllib3 import AuthorizedHttp

class GCPConf:
    """Singleton configuration class."""

    __instance = None

    class __GCPConf:
        """Internal class."""

        def __init__(self, path):
            """Construtor da classe interna."""

            self.parent = str(pathlib.Path(__file__).parent.parent.absolute())
            self.tempdir = self.parent + '/temp'
            if path is None:
                self.path = self.parent + '/auth/auth.json'

            if not os.path.exists(self.path):
                raise ValueError("Nenhum JSON encontrado em '{}'".format(self.path))

            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.path

            # reads the data
            self.credentials, self.project_id = default(
                scopes=['https://www.googleapis.com/auth/cloud-platform'])
            self.std_region = 'southamerica-east1'
            # call this only after std_region
            self.std_zone_uri = self.__get_std_zone()
            self.std_zone = self.get_zone_name(self.std_zone_uri)

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
                data = self.get(url.format(self.project_id, self.std_region))

                if data.status == 200:
                    data = json.loads(data.data)

                if not data['zones']:
                    if verbose:
                        print('No zone available for region {}'.format(
                            self.std_region))
                    return None

                return data['zones'][0]  # returns the first zone
            except Exception as excp:
                if verbose:
                    print('Failed to retrieve region information: {}'.format(excp))
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

        if GCPConf.__instance is None:
            GCPConf.__instance = GCPConf.__GCPConf(path)
            if verbose:
                print('Instantiating new GCPConf')
        elif verbose:
            print('Using same GCPConf in {}'.format(GCPConf.__instance.path))

    def __getattr__(self, attr):
        """Aponta atributos não existentes para os atributos da classe interna."""

        # se a class interna também não tiver, vai lançar uma exceção de atributo
        return getattr(self.__instance, attr)
