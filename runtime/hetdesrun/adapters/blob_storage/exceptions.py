class BlobAdapterException(Exception):
    pass


class ConfigError(BlobAdapterException):
    pass


class MissingConfigError(ConfigError):
    pass


class ConfigIncompleteError(ConfigError):
    pass


class CategoryInvalidError(ConfigError):
    pass


class ThingNodeInvalidError(ConfigError):
    pass


class BucketNameInvalidError(ConfigError):
    pass
