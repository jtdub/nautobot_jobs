"""Job to create a mock data set for testing."""
# from django.contrib.contenttypes.models import ContentType
# from django.utils.text import slugify
from nautobot.extras.jobs import Job
from nautobot.dcim.models import Region, Site
from nautobot.tenancy.models import Tenant
from nautobot.ipam.models import RIR, Aggregate, Prefix
from nautobot.extras.models import Status


name = "Create Demo Data"

STATUS = Status.objects.get(name="Active")
REGIONS = ["Africa", "Antartica", "Asia", "Europe", "North America", "South America"]
SUB_REGIONS = [
    {"name": "Chicago", "parent": "North America"},
    {"name": "Dallas", "parent": "North America"},
    {"name": "Denver", "parent": "North America"},
    {"name": "New York", "parent": "North America"},
    {"name": "San Jose", "parent": "North America"},
    {"name": "Seattle", "parent": "North America"},
    {"name": "Virginia", "parent": "North America"},
]
RIR_NAME = "NTC Internet Registry"
TENANT_NAME = "NTC Widgets"
SITE_ASNS = list(range(64513, 65535))
BACKBONE_ASN = 64512
AGGREGATES = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "192.0.2.0/24"]
SITES = [
    {
        "name": "ord1",
        "time_zone": "US/Central",
        "region": "Chicago",
        "facility": "ord1",
        "asn": SITE_ASNS.pop(),
    },
    {
        "name": "dfw1",
        "time_zone": "US/Central",
        "region": "Dallas",
        "facility": "dfw1",
        "asn": SITE_ASNS.pop(),
    },
    {
        "name": "den1",
        "time_zone": "US/Mountain",
        "region": "Denver",
        "facility": "den1",
        "asn": SITE_ASNS.pop(),
    },
    {
        "name": "jfk1",
        "time_zone": "US/Eastern",
        "region": "New York",
        "facility": "jfk1",
        "asn": SITE_ASNS.pop(),
    },
    {
        "name": "sjc1",
        "time_zone": "US/Pacific",
        "region": "San Jose",
        "facility": "sjc1",
        "asn": SITE_ASNS.pop(),
    },
    {
        "name": "sea1",
        "time_zone": "US/Pacific",
        "region": "Seattle",
        "facility": "sea1",
        "asn": SITE_ASNS.pop(),
    },
    {
        "name": "iad1",
        "time_zone": "US/Eastern",
        "region": "Virginia",
        "facility": "iad1",
        "asn": SITE_ASNS.pop(),
    },
]


def create_regions(regions: list) -> list:
    """Create regions."""
    created_regions = []
    for region in regions:
        if isinstance(region, dict):
            parent_region = region.get("parent")
            region = region.get("name")
        else:
            parent_region = None
        created_regions.append(region)
        parent = Region.objects.get(name=parent_region) if parent_region else None
        if parent:
            new_region, _ = Region.objects.get_or_create(name=region, parent=parent)
        else:
            new_region, _ = Region.objects.get_or_create(name=region)
        new_region.validated_save()

    return created_regions


def create_tenant() -> str:
    """Create Tenant."""
    tenant, _ = Tenant.objects.get_or_create(name=TENANT_NAME)
    tenant.validated_save()

    return TENANT_NAME


def create_rir(rir_name: str) -> str:
    """Create RIR."""
    rir, _ = RIR.objects.get_or_create(name=rir_name, is_private=True)
    rir.validated_save()

    return rir_name


def create_aggregates() -> list:
    """Create network aggregates."""
    rir = RIR.objects.first()
    for aggregate in AGGREGATES:
        aggr, _ = Aggregate.objects.get_or_create(prefix=aggregate, rir=rir)
        aggr.validated_save()

    return AGGREGATES


def create_sites() -> list:
    """Create sites."""
    created_sites = []
    tenant = Tenant.objects.get(name=TENANT_NAME)
    for site in SITES:
        created_sites.append(site["name"])
        region = Region.objects.get(name=site["region"])
        new_site, _ = Site.objects.update_or_create(
            name=site["name"],
            time_zone=site["time_zone"],
            region=region,
            asn=site["asn"],
            facility=site["facility"],
            tenant=tenant,
            status=STATUS,
        )
        new_site.validated_save()
    return created_sites


def assign_prefixes() -> list:
    """Assign a /16 from 10.0.0.0/8 to each site."""
    assigned_prefixes = []
    aggregate = Aggregate.objects.get(prefix="10.0.0.0/8")
    prefixes = list(aggregate.prefix.subnet(prefixlen=16))
    sites = Site.objects.all()

    prefixes.reverse()

    for site in sites:
        prefix, _ = Prefix.objects.get_or_create(
            prefix=prefixes.pop(),
            tenant=Tenant.objects.get(name=TENANT_NAME),
            status=STATUS,
            site=site,
        )
        assigned_prefixes.append(prefix)
        prefix.validated_save()

    return assigned_prefixes


class CreateDemoData(Job):
    """Job to create a demo dataset."""

    class Meta:
        """Meta class for CreateDemoData."""

        name = "Create Demo Data"
        description = "Create a demo data set for testing various aspects of Nautobot."
        label = "Demo Data"

    def run(self, data=None, commit=None):
        """Main function for CreateDemoData."""
        create_regions(regions=REGIONS)
        create_regions(regions=SUB_REGIONS)
        create_rir(RIR_NAME)
        create_aggregates()
        create_tenant()
        create_sites()
        assign_prefixes()
