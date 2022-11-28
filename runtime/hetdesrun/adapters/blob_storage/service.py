from typing import List

from hetdesrun.adapters.blob_storage.models import Blob, Bucket


def get_buckets() -> List[Bucket]:
    return [
        Bucket(id="bucketA", name="Bucket A"),
        Bucket(id="bucketB", name="Bucket B"),
    ]


def get_blobs_in_bucket(bucket_id: str) -> List[Blob]:
    if bucket_id == "bucketA":
        return [
            Blob(
                id="bucketA.blobI",
                name="Blob I",
                bucket_id="bucketA",
                bucket_name="Bucket A",
            ),
            Blob(
                id="bucketA.blobII",
                name="Blob II",
                bucket_id="bucketA",
                bucket_name="Bucket A",
            ),
        ]
    if bucket_id == "bucketB":
        return [
            Blob(
                id="bucketB.blobI",
                name="Blob I",
                bucket_id="bucketB",
                bucket_name="Bucket B",
            ),
            Blob(
                id="bucketB.blobII",
                name="Blob II",
                bucket_id="bucketB",
                bucket_name="Bucket B",
            ),
        ]


def get_all_blobs() -> List(Blob):
    blob_list: List[Blob] = []
    for bucket in get_buckets():
        for blob in get_blobs_in_bucket(bucket.id):
            blob_list.append(blob)
    return blob_list


def get_bucket_by_id(bucket_id: str) -> Bucket:
    if bucket_id == "bucketA":
        return Bucket(id="bucketA", name="Bucket A")
    if bucket_id == "bucketB":
        return Bucket(id="bucketB", name="Bucket B")


def get_blob_by_id(blob_id: str) -> Blob:
    if blob_id == "bucketA.blobI":
        return Blob(
            id="bucketA.blobI",
            name="Blob I",
            bucket_id="bucketA",
            bucket_name="Bucket A",
        )
    if blob_id == "bucketA.blobI":
        return Blob(
            id="bucketA.blobII",
            name="Blob II",
            bucket_id="bucketA",
            bucket_name="Bucket A",
        )
    if blob_id == "bucketB.blobI":
        return Blob(
            id="bucketB.blobI",
            name="Blob I",
            bucket_id="bucketB",
            bucket_name="Bucket B",
        )
    if blob_id == "bucketB.blobI":
        return Blob(
            id="bucketB.blobII",
            name="Blob II",
            bucket_id="bucketB",
            bucket_name="Bucket B",
        )
