"""
Core object for GCP classes.
"""

import json

VALID_MACHINES = [  # beta machines (E2) are not yet ready to be used here
    'n1-standard-1',
    'n1-standard-2',
    'n1-standard-4',
    'n1-standard-8',
    'n1-standard-16',
    'n1-standard-32',
    'n1-standard-64',
    'n1-standard-96',
    'n1-highmem-2',
    'n1-highmem-4',
    'n1-highmem-8',
    'n1-highmem-16',
    'n1-highmem-32',
    'n1-highmem-64',
    'n1-highmem-96',
    'n1-highcpu-2',
    'n1-highcpu-4',
    'n1-highcpu-8',
    'n1-highcpu-16',
    'n1-highcpu-32',
    'n1-highcpu-64',
    'n1-highcpu-96',
    'n2-standard-2',
    'n2-standard-4',
    'n2-standard-8',
    'n2-standard-16',
    'n2-standard-32',
    'n2-standard-48',
    'n2-standard-64',
    'n2-standard-80',
    'n2-highmem-2',
    'n2-highmem-4',
    'n2-highmem-8',
    'n2-highmem-16',
    'n2-highmem-32',
    'n2-highmem-48',
    'n2-highmem-64',
    'n2-highmem-80',
    'n2-highcpu-2',
    'n2-highcpu-4',
    'n2-highcpu-8',
    'n2-highcpu-16',
    'n2-highcpu-32',
    'n2-highcpu-48',
    'n2-highcpu-64',
    'n2-highcpu-80'
]

VALID_JOBS = [
    'hadoop_job',
    'spark_job',
    'pyspark_job',
    'hive_job',
    'pig_job',
    'spark_sql_job'
]

class GCPCore:
    """Base class for Google Compute Engine and Google Cloud Dataproc classes."""

    def __init__(self, objname=None):
        """Constructor."""

        self.objname = objname
        self.__myattrbs = {}

    def add_attr(self, varname, value):
        """Add a attribute."""

        setattr(self, varname, value)
        value = value.get_rep() if isinstance(value, GCPCore) else value
        if isinstance(value, list):
            value = [v.get_rep() if isinstance(v, GCPCore) else v for v in value]
        self.__myattrbs[varname] = value

    def get_rep(self):
        """
        Returns the current representation.

        This method will oftenly be overrided.
        """

        return self.__myattrbs

    def to_json(self):
        """Returns a json representation."""

        if self.objname is None:
            representation = self.__myattrbs
        else:
            representation = {self.objname: self.__myattrbs}

        return json.dumps(representation)

    def __str__(self):
        """to string."""

        return self.to_json()
