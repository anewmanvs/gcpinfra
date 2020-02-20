"""
GCS Communicator.

Upload and manage files. This module configures checksum check using CRC32c hash
for upload verification

In case of errors, re-raise exceptions sent by Google.
"""

# pylint: disable=invalid-name, try-except-raise

import base64
from hashlib import md5
from datetime import datetime

import pandas as pd
from google.cloud import storage
from crc32c import crc32

from gcpinfra.gcp.conf import GCPConf

class GCSComms:
    """
    GCS Communication Manager
    """

    def __init__(self, bucketname, verbose=False):
        """Constructor."""

        self.verbose = verbose
        self.conf = GCPConf(verbose=verbose)
        self.bucketname = bucketname
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucketname)

        self.decode_to = 'utf-8'

    def __print(self, msg):
        """Prints message accordingly to 'verbose' param."""

        if self.verbose:
            print(msg)

    def __perform_crc32c_on_file(self, filename):
        """Creates CRC32c hash for a file."""

        with open(filename, 'rb') as _f:
            checksum = crc32(_f.read())
            base64_crc32c = base64.b64encode(
                checksum.to_bytes(length=4, byteorder='big')).decode(self.decode_to)
        return base64_crc32c

    def __perform_crc32c_on_str(self, _str):
        """Creates CRC32c hash for a string."""

        checksum = crc32(_str.encode())
        base64_crc32c = base64.b64encode(
            checksum.to_bytes(length=4, byteorder='big')).decode(self.decode_to)
        return base64_crc32c

    def __replace_policy(self, blob, gcsfilename, policy):
        """
        Specify actions.

        Please note the credentials specified in GCPConf must have GCS permissions.

        Policies:
            - 'raise' will delegate the file's override authority to GCS
            - 'ignore' in case the file exists do nothing
            - 'replace' deletes the existing file and uploads a new one
        """

        if policy == 'raise':
            return True

        exists = self.file_exists(gcsfilename=gcsfilename, blob=blob)
        if policy == 'ignore':
            if exists:
                self.__print('File already exists and upload will be ignored')
                return False
            return True

        if policy == 'replace':
            if exists:
                self.delete_file(gcsfilename=gcsfilename, blob=blob)
                self.__print('File already exists and will be replaced')
            return True

        raise ValueError("Invalid policy '{}'".format(policy))

    def get_file_rep(self, gcsfilename):
        """Returns file blob."""

        blob = self.bucket.get_blob(gcsfilename)
        if blob is None:
            return self.bucket.blob(gcsfilename)
        return blob

    def file_exists(self, gcsfilename=None, blob=None):
        """Check if file exists in bucket."""

        if blob is None:
            blob = self.get_file_rep(gcsfilename)

        return blob.exists()

    def delete_file(self, gcsfilename=None, blob=None):
        """
        Delete file from bucket.

        If file does not exist, raises an exception
        """

        if blob is None:
            blob = self.get_file_rep(gcsfilename)

        blob.delete()

    def find_blobs_by_prefix(self, prefix):
        """
        Find blobs by prefix.

        In GCS there is no such thing as a directory. Dirs or folders are just
        prefixes of objects

        Also bear in mind that this method gets slower the more objects are
        contained in the prefix.
        """

        blobs = []
        _blobs = self.storage_client.list_blobs(self.bucketname, prefix=prefix)
        for _blob in _blobs:
            blobs.append(_blob)
        return blobs

    def delete_multiples(self, bloblist):
        """
        Delete multiples objects from bucket.

        Also bear in mind that this method gets slower the more objects are
        contained in the list.

        The list must contain just valid blobs.
        """

        for blob in bloblist:
            blob.delete()

    def upload_file(self, filename, gcsfilename, replacepolicy='raise'):
        """Uploads a file."""

        crc32c = self.__perform_crc32c_on_file(filename)
        self.__print('Uploading file {} to {}'.format(filename, gcsfilename))
        blob = self.get_file_rep(gcsfilename)
        if self.__replace_policy(blob, gcsfilename, replacepolicy):
            blob.crc32c = crc32c
            blob.upload_from_filename(filename)
            self.__print('File {} uploaded'.format(gcsfilename))

    def upload_dataframe(self, df, gcsfilename, replacepolicy='raise',
                         extension='parquet'):
        """
        Uploads a pandas dataframe.

        Param. 'df' should be a pandas.DataFrame
        If 'parquet' extension is selected, a temp file will be created and uploaded
        to GCS.
        """

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Param. 'df' should be a 'pandas.DataFrame'.")

        if extension == 'csv':
            self.__print('Uploading {} rows to csv in {}'.format(
                df.shape[0], gcsfilename))
            blob = self.get_file_rep(gcsfilename)
            _str = df.to_csv(index=False)
            crc32c = self.__perform_crc32c_on_str(_str)
            if self.__replace_policy(blob, gcsfilename, replacepolicy):
                blob.crc32c = crc32c
                blob.upload_from_string(_str, content_type='text/plain')
                self.__print('File {} uploaded'.format(gcsfilename))
        elif extension == 'parquet':
            filename = '{}/temp{}.parquet'.format(
                self.conf.tempdir, md5(str(datetime.now()).encode()).hexdigest())
            df.to_parquet(filename)
            try:
                self.upload_file(filename, gcsfilename, replacepolicy)
            except:
                raise
            finally:
                self.conf.remove(filename)
        else:
            raise ValueError("Not supported extension '{}'".format(extension))
