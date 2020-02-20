"""
Represents a Google Cloud Dataproc Workflow
"""

# pylint: disable=too-few-public-methods, too-many-arguments
# pylint: disable=too-many-instance-attributes

import json
from warnings import warn

from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.gapic.transports import \
    workflow_template_service_grpc_transport as wtsgt
from google.api_core.exceptions import GoogleAPICallError

from gcpinfra.gcp.conf import GCPConf
from gcpinfra.gcd.jobs import GCDJob
from gcpinfra.gce.clusters import GCECluster

class GCDWorkflow:
    """
    Google Cloud Dataproc Workflow.

    Creates an ephemeral cluster to run DAGs. After everything is processed, the
    cluster will end its life cycle.

    Please note that jobs are not sequential unless you configure it with a list of
    'prerequisiteStepIds'. Refer to http://bit.ly/google-job-prerequisiteStepIds
    for more details.
    """

    def __init__(self, jobs=None, cluster=None, verbose=False):
        """Constructor."""

        self.conf = GCPConf(verbose=verbose)  # must configure this first

        self.verbose = verbose
        self.jobs = jobs
        self.__validate_jobs()
        self.cluster = cluster

        if not isinstance(cluster, GCECluster):
            raise ValueError("Param 'cluster' must be an instance of "
                             "'gcpinfra.gcecluster.GCECluster'")

        self.zone_uri = self.cluster.zone_uri
        self.region = self.__get_region()
        self.dataproc_workflow_client = self.__get_workflow_client(self.region)

        self.state = 'built'
        self.result = None

    def __print(self, msg):
        """Print msg accordingly to verbose parameter."""

        if self.verbose:
            print(msg)

    def __validate_jobs(self):
        """Verifies if jobs are valid."""

        msg = "Param 'jobs' must be either 'list' of, or single, "
        msg += "'gcpinfra.gcdjobs.GCDJob'"
        if not isinstance(self.jobs, (GCDJob, list)):
            raise ValueError(msg)

        if not isinstance(self.jobs, list):  # there is a single job passed
            self.jobs = [self.jobs]

        for job in self.jobs:
            if not isinstance(job, GCDJob):
                raise ValueError(msg)

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
        except GoogleAPICallError:
            self.result = None

        self.state = 'done'
        result = 'success' if self.result is not None else 'failed'
        self.__print('[{}] Workflow finished ({})'.format(sync, result))

    def run(self, sync=True):
        """
        Execute this workflow.

        You should not wait as it may take several minutes
        to complete. Most implementations will do a while True but that takes your
        CPU to 100% and increase its temperature.
        """

        self.state = 'running'
        ssync = 'sync' if sync else 'async'
        self.__print('Initiating workflow [{}]. Check '
                     'https://console.cloud.google.com/dataproc/workflows/'.format(
                        ssync))

        parent = 'projects/{}/regions/{}'.format(self.conf.project_id, self.region)
        wf = self.dataproc_workflow_client.instantiate_inline_workflow_template(
            parent, self.mount_json_representation())

        if sync:
            self.__async_result(wf, sync=ssync)
            return self.result
        else:
            wf.add_done_callback(self.__async_result)
            return None
