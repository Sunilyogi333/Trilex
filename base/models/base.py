from base.models.soft_delete import SoftDelete
from base.models.timestamp import Timestamps
from base.models.uuid import UUIDPrimaryKey


class AbstractBaseModel(UUIDPrimaryKey, Timestamps, SoftDelete):

    class Meta:
        abstract = True
