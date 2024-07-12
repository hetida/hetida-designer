import json
import logging
import os
import re
import unicodedata
from pathlib import Path

from hetdesrun.component.code import expand_code
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import Type

logger = logging.getLogger(__name__)


def slugify(value: str, allow_unicode: bool = False) -> str:
    """Sanitize string to make it usable as a file name

    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def save_transformation_into_directory(
    transformation_revision: TransformationRevision,
    directory_path: str,
    components_as_code: bool = False,
    expand_component_code: bool = False,
) -> str:
    """Save single trafo as json file at the appropriate place in a directory structure

    The directory structure is

    direcotory_path
        /components
            /Category
                /TRAFONAME_SLUGIFIEDTAG_TRAFOID.json
        /workflows
            /Category
                /TRAFONAME_SLUGIFIEDTAG_TRAFOID.json

    where SLUGIFIEDTAG is somthing like 101 for a tag 1.0.1

    Returns the path of the saved file.
    """
    # Create directory on local system
    category_directory = os.path.join(
        directory_path,
        transformation_revision.type.lower() + "s",
        slugify(transformation_revision.category),
    )
    Path(category_directory).mkdir(parents=True, exist_ok=True)

    file_extension = (
        ".json"
        if components_as_code is False or transformation_revision.type == Type.WORKFLOW
        else ".py"
    )

    # infer file path
    path = os.path.join(
        category_directory,
        slugify(transformation_revision.name)
        + "_"
        + slugify(transformation_revision.version_tag)
        + "_"
        + str(transformation_revision.id).lower()
        + file_extension,
    )

    if expand_component_code and transformation_revision.type == Type.COMPONENT:
        transformation_revision.content = expand_code(transformation_revision)

    # Save the transformation revision
    with open(path, "w", encoding="utf8") as f:
        try:
            if file_extension == ".json":
                json.dump(
                    json.loads(transformation_revision.json(exclude_none=True)),
                    f,
                    indent=2,
                    sort_keys=True,
                )
                logger.info(
                    "exported %s '%s' to %s",
                    transformation_revision.type,
                    transformation_revision.name,
                    path,
                )
            else:
                assert isinstance(  # hint for mypy # noqa: S101
                    transformation_revision.content, str
                )
                f.write(transformation_revision.content)
        except KeyError:
            logger.error(
                "Could not safe the %s with id %s on the local system.",
                transformation_revision.type,
                str(transformation_revision.id),
            )
    return path
