"""
Represents a machine in GCE and its configurations.

Those representations will be used during cluster configuration.

Refer to https://cloud.google.com/compute/docs/machine-types for detailed
information
"""

# pylint: disable=too-few-public-methods, invalid-name, too-many-arguments

from gcpinfra.gcp.core import VALID_MACHINES, GCPCore

def valid_machine_type(machine_type):
    """Checks if the informed machine type is valid or not."""

    return machine_type in VALID_MACHINES

class GCEDisk(GCPCore):
    """
    Represents a google compute engine disk.
    """

    def __init__(self, disk_type=None, size=None, num_local_ssds=0):
        """Constructor."""

        super().__init__()
        self.add_attr('boot_disk_type', 'pd-ssd' if disk_type is None else disk_type)
        self.add_attr('boot_disk_size_gb', 15 if size is None else size)
        self.add_attr('num_local_ssds', num_local_ssds)

class GCEMachine(GCPCore):
    """
    Represents a google compute engine machine.
    """

    def __init__(self, machine_type=None, instances=1, disk=None,
                 accelerators=None):
        """Constructor."""

        machine_type = 'n1-standard-1' if machine_type is None else machine_type
        disk = GCEDisk('pd-ssd', 15, 0) if disk is None else disk
        accelerators = [] if accelerators is None else accelerators

        if not isinstance(disk, GCEDisk):
            raise ValueError("Param 'disk' must be an instance of "
                             "'gcpinfra.gcpcore.GCEDisk'")

        if not valid_machine_type(machine_type):
            raise ValueError("Param 'machine_type' ('{}') is not valid. Check "
                             "https://cloud.google.com/compute/docs/machine-types "
                             "for detailed information.".format(machine_type))

        super().__init__()
        self.add_attr('num_instances', instances)
        self.add_attr('machine_type_uri', machine_type)
        self.add_attr('disk_config', disk)
        self.add_attr('accelerators', accelerators)
