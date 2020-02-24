"""
Represents a job to be run in a cluster or machine.

Here you will find implementations for each type of job.
"""

# pylint: disable=invalid-name, too-few-public-methods, too-many-arguments

from gcpinfra.gcp.core import GCPCore, VALID_JOBS

def valid_job_type(job_type):
    """Checks if the informed job type is valid or not."""

    return job_type in VALID_JOBS

def check_param_type(p, t, ignore_none=False, param_name=''):
    """Checks if the informed param is the correct type."""

    if ignore_none and p is None:
        return

    if not isinstance(p, t):
        raise ValueError("Param. '{}' must be a '{}'".format(param_name, t))

def check_list_type(l, t, ignore_none=False, param_name=''):
    """Checks if only the correct type is present in list values"""

    if ignore_none and l is None:
        return

    if any(map(lambda x: not isinstance(x, t), l)):
        raise ValueError("Param. '{}' must be filled with values of '{}'".format(
            param_name, t))

def nelnn(param):
    """Return true if 'param' is neither an empty list or none."""

    if not isinstance(param, list) and param is not None:
        return True

    return bool(param)

class GCDJob(GCPCore):
    """Generic Job."""

    def __init__(self, step_id, job_type):
        """Constructor."""

        if not valid_job_type(job_type):
            raise ValueError("Param 'job_type' is not valid. Check "
                             "https://cloud.google.com/dataproc/docs/reference/"
                             "rest/v1/projects.locations.workflowTemplates"
                             "#orderedjob for detailed information.")

        super().__init__()
        self.add_attr('step_id', step_id)
        self.job_type = job_type

    def add_conf(self, conf):
        """Adds job configuration."""

        check_param_type(conf, dict, param_name='conf')
        conf = {key: conf[key] for key in conf if nelnn(conf[key])}
        self.add_attr(self.job_type, conf)

class GCDPySparkJob(GCDJob):
    """
    PySpark Job.

    More info: https://cloud.google.com/dataproc/docs/reference/rest/v1/PySparkJob
    """

    def __init__(self, step_id, main, args=None, python_files=None, jar_files=None,
                 other_files=None, archive_files=None, properties=None):
        """Constructor."""

        check_param_type(main, str, param_name='main')  # required
        check_param_type(step_id, str, param_name='step_id')  # required

        # optionals
        check_param_type(args, list, ignore_none=True, param_name='args')
        check_param_type(jar_files, list, ignore_none=True, param_name='jar_files')
        check_param_type(python_files, list, ignore_none=True,
                         param_name='python_files')
        check_param_type(other_files, list, ignore_none=True,
                         param_name='other_files')
        check_param_type(archive_files, list, ignore_none=True,
                         param_name='archive_files')
        check_param_type(properties, dict, ignore_none=True,
                         param_name='properties')

        # check for correct internal type
        check_list_type(args, str, ignore_none=True, param_name='args')
        check_list_type(jar_files, str, ignore_none=True, param_name='jar_files')
        check_list_type(python_files, str, ignore_none=True,
                        param_name='python_files')
        check_list_type(other_files, str, ignore_none=True,
                        param_name='other_files')
        check_list_type(archive_files, str, ignore_none=True,
                        param_name='archive_files')

        conf = {
            'main_python_file_uri': main,
            'args': args,
            'python_file_uris': python_files,
            'jar_file_uris': jar_files,
            'file_uris': other_files,
            'archive_uris': archive_files,
            'properties': properties
        }

        super().__init__(step_id, 'pyspark_job')
        self.add_conf(conf)
