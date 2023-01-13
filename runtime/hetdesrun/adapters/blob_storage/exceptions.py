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


class S3Error(BlobAdapterException):
    pass


class InvalidS3Endpoint(S3Error):
    pass


class BucketNotFound(S3Error):
    pass
