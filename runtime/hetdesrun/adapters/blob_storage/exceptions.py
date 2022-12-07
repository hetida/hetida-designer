class BlobAdapterException(Exception):
    pass


class ConfigError(BlobAdapterException):
    pass


class StructureError(BlobAdapterException):
    pass


class MissingConfigError(ConfigError):
    pass


class ThingNodeInvalidError(ConfigError):
    pass


class BucketNameInvalidError(ConfigError):
    pass


class SourceNotFound(StructureError):
    pass


class SourcesNotUnique(StructureError):
    pass


class SinkNotFound(StructureError):
    pass


class SinksNotUnique(StructureError):
    pass


class ThingNodeNotFound(StructureError):
    pass


class ThingNodesNotUnique(StructureError):
    pass
