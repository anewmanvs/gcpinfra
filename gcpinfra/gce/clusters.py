"""
Create clusters to run jobs.

A bunch of configurations are not yet ready to be used.
"""

# pylint: disable=too-few-public-methods, too-many-arguments
# pylint: disable=too-many-instance-attributes

from gcpinfra.gcp.core import GCPCore
from gcpinfra.gce.conf import GCEMachine, GCEDisk

def std_machine(instances=1):
    """Standard machine."""

    return GCEMachine(machine_type='n1-standard-1',
                      instances=instances, accelerators=None,
                      disk=GCEDisk(disk_type='pd-ssd', size=15, num_local_ssds=0))

class GCECluster(GCPCore):
    """
    Cluster to run jobs.

    User must inform the cluster name, configurations and zone to run.
    """

    def __init__(self, cluster_name, master_config=None, worker_config=None,
                 zone_uri=None, image=None, properties=None):
        """Constructor."""

        if not isinstance(cluster_name, str):
            raise ValueError("Param 'cluster_name' must be 'str'")

        self.master_config = master_config
        self.worker_config = worker_config
        if self.master_config is None:
            self.master_config = std_machine()
        if self.worker_config is None:
            self.worker_config = std_machine(instances=2)
        # must always follow master and worker attribution
        self.__validate_machine_configuration()
        self.zone_uri = zone_uri

        if image is None:
            image = '1.3-deb9'

        if properties is None:
            properties = {}

        super().__init__()
        self.add_attr('cluster_name', cluster_name)
        config = {
            'gce_cluster_config': {'zone_uri': zone_uri},
            'master_config': self.master_config.get_rep(),
            'worker_config': self.worker_config.get_rep(),
            'software_config': {
                'image_version': image,
                'properties': properties
            },
            'secondary_worker_config': {
                'num_instances': 0, 'is_preemptible': True
            }
        }
        self.add_attr('config', config)

    def __validate_machine_configuration(self):
        """Verifies if machine is valid."""

        if not isinstance(self.master_config, GCEMachine):
            raise ValueError("Param 'master_config' must be an instance of "
                             "'gcpinfra.gceconf.GCEMachine'")
        if not isinstance(self.worker_config, GCEMachine):
            raise ValueError("Param 'worker_config' must be an instance of "
                             "'gcpinfra.gceconf.GCEMachine'")
