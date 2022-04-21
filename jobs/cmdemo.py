"""Job to create a data set for demoing the Circuit Maintenance Plugin."""
from nautobot.extras.jobs import Job
from nautobot.dcim.models import (
    Site,
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Interface,
    Cable,
)
from nautobot.extras.models import Status
from nautobot.circuits.models import Provider, Circuit, CircuitType, CircuitTermination


STATUS = Status.objects.get(name="Active")


def create_site() -> Site:
    """Create the NTC Corp Site."""
    site, _ = Site.objects.update_or_create(
        name="NTC Corp", status=STATUS, asn=64512, time_zone="America/New_York"
    )
    return site


def create_device() -> Device:
    """Create the NTC Corp Device."""
    device_role, _ = DeviceRole.objects.update_or_create(name="Internet Edge")
    manufacturer, _ = Manufacturer.objects.update_or_create(name="Cisco Systems")
    device_type, _ = DeviceType.objects.update_or_create(
        manufacturer=manufacturer, model="CSRv"
    )

    device, _ = Device.objects.update_or_create(
        name="csr3",
        device_role=device_role,
        device_type=device_type,
        site=create_site(),
        status=STATUS,
    )

    for item in ["GigabitEthernet2", "GigabitEthernet3"]:
        Interface.objects.update_or_create(
            device=device,
            name=item,
            type="1000base-t",
            enabled=True,
        )

    return device


def create_providers() -> list:
    """Create Providers."""
    provider_data = [{"name": "Lumen", "asn": 3356}, {"name": "NTT", "asn": 2914}]
    providers = []

    for item in provider_data:
        provider, _ = Provider.objects.update_or_create(
            name=item["name"], asn=item["asn"]
        )
        providers.append(provider)
    return providers


def create_circuits() -> list:
    """Create Provider Circuits."""
    transit, _ = CircuitType.objects.update_or_create(name="Transit")
    providers = create_providers()
    circuits = []
    i = 0

    for cid in ["12/NTC/01234/AB", "09/NTC/9876/DC"]:
        circuit, _ = Circuit.objects.update_or_create(
            cid=cid,
            provider=providers[i],
            type=transit,
            status=STATUS,
        )
        circuits.append(circuit)
        i += 1

    for item in circuits:
        CircuitTermination.objects.update_or_create(
            circuit=item, term_side="A", site=Site.objects.get(name="NTC Corp")
        )

    return circuits


def connect_cable(device, circuit) -> Cable:
    """Connect a circuit to a device."""
    cable, _ = Cable.objects.update_or_create(
        termination_a_type="circuits.circuittermination",
        termination_a_id=circuit,
        termination_b_type="dcim.interface",
        termination_b_id=device,
        type="smf",
        status=STATUS,
    )
    return cable


class CreateCMDemoData(Job):
    """Job to create a data set for demoing the Circuit Maintenance Plugin."""

    class Meta:
        """Meta class for CreateDMDemoData."""

        name = "Create Circuit Maintenance Demo Data"
        description = (
            "Create a demo data set for testing the Circuit Maintenance Plugin."
        )
        label = "Circuit Maintenance Demo Data"

    def run(self, data=None, commit=None):
        """Main function for CreateDemoData."""
        device = create_device()
        circuits = create_circuits()

        for item in circuits:
            connect_cable(device, item.pk)
