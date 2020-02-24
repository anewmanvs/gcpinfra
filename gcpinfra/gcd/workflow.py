"""
Represents a Google Cloud Dataproc Workflow
"""

# pylint: disable=too-few-public-methods, too-many-arguments
# pylint: disable=too-many-instance-attributes

import re
import json
from warnings import warn

from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.gapic.transports import \
    workflow_template_service_grpc_transport as wtsgt
from google.cloud.dataproc_v1.proto import workflow_templates_pb2
from google.protobuf import empty_pb2
from google.api_core.operation import from_http_json
from google.api_core.exceptions import GoogleAPICallError
from googleapiclient import discovery

from gcpinfra.gcp.conf import GCPConf
from gcpinfra.gcd.jobs import GCDJob
from gcpinfra.gce.clusters import GCECluster

class GCDWorkflow:
    """
    Google Cloud Dataproc Inline Workflow.

    Creates an ephemeral cluster to run DAGs. After everything is processed, the
    cluster will end its life cycle.

    Please note that jobs are not sequential unless you configure it with a list of
    'prerequisiteStepIds'. Refer to http://bit.ly/google-job-prerequisiteStepIds
    for more details.
    """

    def __init__(self, jobs=None, cluster=None, verbose=False, opname=None,
                 sync=True, callback=None, **kwargs):
        """
        Instantiate an inline workflow.

        This workflow will not be saved with a name. The only way to access it from
        outside is using the operation name.

        This classe requires that either 'jobs' and 'cluster' or 'opname' are
        provided. This means that if you pass 'opname' you cannot pass 'jobs' or
        'cluster'.

        When 'opname' is provided this class represents a previously created
        workflow and will raise an exception if name isn't found in dataproc.
        Param 'opname' must respect the template:
        projects/{project_id}/regions/{region}/operations/{op_uuid}

        Args:
            jobs (list[gcpinfra.gcd.jobs.GCDJob]): Job list to run when
                the cluster starts.
            cluster (gcpinfra.gce.cluster.GCECluster): Cluster that will be created
                and deleted after jobs finish.
            verbose (bool): Optional. Starts in verbose mode.
            opname (str): Optional. Operation name to retrieve the inline workflow
            sync (bool): Optional. Indicating if method 'run' is sync
            callback (callable): Optional. Callable to be invoked when async.
                First arg must always be a bool indicating whether or not the
                execution failed. Second arg must always the result. In case of
                failure, the result will be None. The result type depends on the
                job you executed.
            kwargs (dict): Optional. Params to pass to callback
        """

        self.conf = GCPConf(verbose=verbose)  # must configure this first
        self.verbose = verbose
        self.opname = opname
        self.result = None
        self.sync = sync
        self.callback = callback
        self.callbackkwargs = kwargs
        self.failed = None

        if not self.sync and callback is not None and not callable(callback):
            raise ValueError("Arg 'callback' must be callable.")

        if self.sync and callback is not None:
            warn("Provided arg 'callback' will not be used since arg 'sync'"
                 " is True")

        if opname is not None and any([x is not None for x in [jobs, cluster]]):
            raise ValueError("Arg 'opname' provided with args 'jobs' and 'cluster'."
                             " You can only pass either 'jobs' and 'cluster'"
                             " or 'opname'.")
        elif opname is None:  # use jobs and cluster
            if not isinstance(cluster, GCECluster):
                raise ValueError("Arg 'cluster' must be an instance of "
                                 "'gcpinfra.gcecluster.GCECluster'")

            self.jobs = self.__validate_jobs(jobs)
            self.cluster = cluster

            self.zone_uri = self.cluster.zone_uri
            self.region = self.__get_region()
            self._wf = None
            self._origin_user = True
        else:  # use opname
            self.jobs = None
            self.cluster = None
            self.zone_uri = None
            self.region = self.__get_region_from_opname()
            self.dataproc_workflow_client = None
            self._wf = self.__get_operation_dict()
            self._origin_user = False

        self.dataproc_workflow_client = self.__get_workflow_client(self.region)

    def __print(self, msg):
        """Print msg accordingly to verbose parameter."""

        if self.verbose:
            print(msg)

    def __get_region_from_opname(self):
        """Retrieve the region from the opname."""

        return re.match(r'.*/regions/(.+)/operations.*', self.opname).group(1)

    def __get_operation_dict(self):
        """Returns a dict representing the operation using the opname."""

        self.__print("Retrieving operation '{}'".format(self.opname))
        s = discovery.build('dataproc', 'v1', credentials=self.conf.credentials)
        opdict = s.projects().regions().operations().get(name=self.opname).execute()
        return from_http_json(opdict, self.conf.request, empty_pb2.Empty,
                              metadata_type=workflow_templates_pb2.WorkflowTemplate)

    def __validate_jobs(self, jobs):
        """Verifies if jobs are valid."""

        msg = "Param 'jobs' must be either 'list' of, or single, "
        msg += "'gcpinfra.gcdjobs.GCDJob'"
        if not isinstance(jobs, (GCDJob, list)):
            raise ValueError(msg)

        if not isinstance(jobs, list):  # there is a single job passed
            jobs = [jobs]

        for job in jobs:
            if not isinstance(job, GCDJob):
                raise ValueError(msg)

        return jobs

    def __get_region(self):
        """Returns the region based on the zone."""

        if self.zone_uri is None:
            self.cluster.zone_uri = self.conf.std_zone_uri
            self.zone_uri = self.conf.std_zone_uri

        zone = self.conf.get_zone_name(self.zone_uri)
        try:
            region = '-'.join(zone.split('-')[:-1])
            self.__print("Using region '{}'".format(region))
            return region
        except:
            raise ValueError("Invalid zone '{}'".format(zone))

    def __get_workflow_client(self, region):
        """Based on the region, returns the dataproc workflow client."""

        if region == 'global':  # use the global configuration
            self.__print("Using global region configuration")
            return dataproc_v1.WorkflowTemplateServiceClient()

        client_transport = wtsgt.WorkflowTemplateServiceGrpcTransport(
            address="{}-dataproc.googleapis.com:443".format(region))
        return dataproc_v1.WorkflowTemplateServiceClient(client_transport)

    def mount_json_representation(self, return_type='rep'):
        """Generates JSON representation for the workflow."""

        rep = {
            'placement': {'managed_cluster': self.cluster.get_rep()},
            'jobs': [j.get_rep() for j in self.jobs]
        }

        if return_type == 'rep':
            return rep
        elif return_type == 'str':
            return json.dumps(rep)

        raise ValueError("Param. 'return_type' must be either 'rep' or 'str'.")

    def __async_result(self, future, sync='async'):
        """Get async result from worflow execution."""

        try:
            self.result = future.result()
            self.failed = False
        except GoogleAPICallError:
            self.result = None
            self.failed = True

        if self.callback is not None and not self.sync:
            self.callback(self.failed, self.result, **self.callbackkwargs)

        result = 'success' if self.result is not None else 'failed'
        self.__print('[{}] Workflow finished ({})'.format(sync, result))

    def run(self, sync=None):
        """
        Execute this workflow.
        """

        if sync is not None:
            warn("Arg 'sync' of method 'run' is deprecated. Please use arg"
                 " 'sync' in the constructor.", DeprecationWarning)

        ssync = 'sync' if self.sync else 'async'
        if self._origin_user:
            self.__print('Initiating workflow [{}]. Check '
                         'https://console.cloud.google.com/dataproc/'
                         'workflows/'.format(ssync))

            parent = 'projects/{}/regions/{}'.format(self.conf.project_id,
                                                     self.region)
            wf = self.dataproc_workflow_client.instantiate_inline_workflow_template(
                parent, self.mount_json_representation())
            self._wf = wf
            self.opname = self._wf.operation.name

        if self.sync:
            self.__async_result(self._wf, sync=ssync)
            return self.result
        else:
            self._wf.add_done_callback(self.__async_result)
            return None

    def running(self):
        """Return true in case the workflow is running."""

        if self._wf is not None:
            return self._wf.running()

        return False

    def done(self):
        """Return true in case the workflow is done."""

        if self._wf is not None:
            return self._wf.done()

        return False
