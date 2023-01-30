class BlobAdapterException(Exception):
    pass


class HierarchyError(BlobAdapterException):
    pass


class StructureError(BlobAdapterException):
    pass


class MissingHierarchyError(HierarchyError):
    pass


class BucketNameInvalidError(HierarchyError):
    pass


class SourceNotFound(StructureError):
    pass


class SourceNotUnique(StructureError):
    pass


class SinkNotFound(StructureError):
    pass


class SinkNotUnique(StructureError):
    pass


class ThingNodeNotFound(StructureError):
    pass


class ThingNodeNotUnique(StructureError):
    pass


class NoAccessTokenAvailable(BlobAdapterException):
    pass


class S3Error(BlobAdapterException):
    pass


class InvalidEndpoint(S3Error):
    pass


class BucketNotFound(S3Error):
    pass


class ObjectNotFound(S3Error):
    pass


class ObjectExists(S3Error):
    pass


class UnexpectedClientError(S3Error):
    pass
