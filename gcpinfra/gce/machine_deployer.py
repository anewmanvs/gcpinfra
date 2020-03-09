"""
Machine deployer

Deploy a GCE machine with the informed params
"""

from googleapiclient import discovery

from gcpinfra.gcp.conf import GCPConf
from gcpinfra.gce.conf import GCEMachine

# pylint: disable=invalid-name

class GCEMachineDeployer:
    """
    Represents a machine deployer.
    """

    def __init__(self, name, zone, machine, docker_image, restart_policy='Always'):
        """Constructor."""

        self.conf = GCPConf()

        self.machine = machine
        self.name = name
        self.zone = zone
        self.docker_image = docker_image
        self.restart_policy = restart_policy
        self.region = self.__get_region()  # only after zone declaration

        if self.restart_policy not in ['OnFailure', 'Never', 'Always']:
            raise ValueError("Invalid 'restart_policy' value")

        if not isinstance(self.machine, GCEMachine):
            raise ValueError("Expected a machine 'GCEMachine' got '{}'".format(
                type(self.machine)))

    def __get_region(self):
        """Returns the region."""

        return '-'.join(self.zone.split('-')[:-1])

    def instantiate(self):
        """Deploy a machine."""

        compute = discovery.build('compute', 'v1')
        compute.instances().insert(
            project=self.conf.project_id, zone=self.zone,
            body=self.mount_representation()).execute()

    def mount_representation(self):
        """Mount this object representation."""

        _rep = {
            'kind': 'compute#instance',
            'name': self.name,
            'zone': 'projects/{}/zones/{}'.format(self.conf.project_id, self.zone),
            'machineType': 'projects/{}/zones/{}/machineTypes/{}'.format(
                self.conf.project_id, self.zone, self.machine.machine_type_uri),
            'displayDevice': {'enableDisplay': False},
            'metadata': {
                'kind': 'compute#metadata',
                'items': [
                    {
                        'key': 'gce-container-declaration',
                        'value': 'spec:\n  containers:\n    - name: {}\n      ' \
                                 'image: {}\n      stdin: false\n      tty: ' \
                                 'false\n  restartPolicy: {}\n\n# This container' \
                                 ' declaration format is not public API and may ' \
                                 'change without notice. Please\n# use gcloud ' \
                                 'command-line tool or Google Cloud Console to ' \
                                 'run Containers on Google Compute Engine.'.format(
                                    self.name, self.docker_image,
                                    self.restart_policy)
                    },
                    {
                        'key': 'google-logging-enabled',
                        'value': 'true'
                    }
                ]
            },
            'tags': {'items': []},
            'disks': [
                {
                    'kind': 'compute#attacheDisk',
                    'type': 'PERSISTENT',
                    'boot': True,
                    'mode': 'READ_WRITE',
                    'autoDelete': True,
                    'deviceName': self.name,
                    'initializeParams': {
                        'sourceImage': ('projects/cos-cloud/global/images/'
                                        'cos-stable-80-12739-91-0'),
                        'diskType': 'projects/{}/zones/{}/diskTypes/{}'.format(
                            self.conf.project_id, self.zone,
                            self.machine.disk_config.boot_disk_type),
                        'diskSizeGb': '{}'.format(
                            self.machine.disk_config.boot_disk_size_gb)
                    },
                    'diskEncryptionKey': {}
                }
            ],
            'canIpForward': False,
            'networkInterfaces': [
                {
                    'kind': 'compute#networkInterface',
                    'subnetwork': 'projects/{}/regions/{}/subnetworks/default'.format(
                        self.conf.project_id, self.region),
                    'accessConfigs': [
                        {
                            'kind': 'compute#accessConfig',
                            'name': 'External NAT',
                            'type': 'ONE_TO_ONE_NAT',
                            'networkTier': 'PREMIUM'
                        }
                    ],
                    'aliasIpRanges': []
                }
            ],
            'description': '',
            'labels': {'container-vm': 'cos-stable-80-12739-91-0'},
            'scheduling': {
                'preemptible': False,
                'onHostMaintenance': 'MIGRATE',
                'automaticRestart': True,
                'nodeAffinities': []
            },
            'deletionProtection': False,
            'reservationAffinity': {'consumeReservationType': 'ANY_RESERVATION'},
            'serviceAccounts': [
                {
                    'email': self.conf.credentials.service_account_email,
                    'scopes': self.conf.scopes
                }
            ],
            'shieldedInstanceConfig': {
                'enableSecureBoot': False,
                'enableVtpm': True,
                'enableIntegrityMonitoring': True
            }
        }
        return _rep
