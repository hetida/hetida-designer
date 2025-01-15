import os

from pydantic import BaseSettings, Field, validator

from hetdesrun.structure.models import CompleteStructure


class VirtualStructureAdapterConfig(BaseSettings):
    active: bool = Field(
        True,
        description="Whether to register the adapter or not",
        env="VST_ADAPTER_ACTIVE",
    )

    prepopulate_virtual_structure_adapter_at_designer_startup: bool = Field(
        False,
        description="Set this flag to True, if you wish to provide a structure "
        "for the virtual structure adapter "
        "via the field structure_to_prepopulate_virtual_structure_adapter.",
        env="PREPOPULATE_VST_ADAPTER_AT_HD_STARTUP",
    )

    prepopulate_virtual_structure_adapter_via_file: bool = Field(
        False,
        description="Set this flag to True, if you wish to provide a structure "
        "for the virtual structure adapter "
        "via a filepath stored in the "
        "field structure_filepath_to_prepopulate_virtual_structure_adapter.",
        env="PREPOPULATE_VST_ADAPTER_VIA_FILE",
    )

    completely_overwrite_an_existing_virtual_structure_at_hd_startup: bool = Field(
        True,
        description="Determines whether a potentially existent virtual structure in the database "
        "is overwritten (if set to True) or updated (if set to False) "
        "at hetida designer backend startup.",
        env="COMPLETELY_OVERWRITE_EXISTING_VIRTUAL_STRUCTURE_AT_HD_STARTUP",
    )

    structure_filepath_to_prepopulate_virtual_structure_adapter: str | None = Field(
        None,
        description="A JSON-filepath, used to provide a structure "
        "for the virtual structure adapter at hetida designer backend startup. "
        "Used analogously to structure_to_prepopulate_virtual_structure_adapter.",
        env="STRUCTURE_FILEPATH_TO_PREPOPULATE_VST_ADAPTER",
    )

    structure_to_prepopulate_virtual_structure_adapter: CompleteStructure | None = Field(
        None,
        description="A JSON, used to provide a structure for the virtual structure adapter "
        "at hetida designer backend startup. "
        "This built-in adapter enables the user to create "
        "a flexible, abstract hierarchical structure for their data. "
        "In this JSON the user can provide names, descriptions and metadata "
        "for each element of the hierarchy. "
        "The JSON should contain definitions for all thingnodes, sources, sinks and element types "
        "representing the users data.",
        env="STRUCTURE_TO_PREPOPULATE_VST_ADAPTER",
    )

    @validator("structure_filepath_to_prepopulate_virtual_structure_adapter")
    def filepath_must_be_set_when_populating_from_file(
        cls, value: str | None, values: dict
    ) -> str | None:
        if values.get("prepopulate_virtual_structure_adapter_via_file") and (
            value is None or value == ""
        ):
            raise ValueError(
                "structure_filepath_to_prepopulate_virtual_structure_adapter must be set "
                "if prepopulate_virtual_structure_adapter_via_file is set to True"
            )
        return value

    @validator("structure_to_prepopulate_virtual_structure_adapter")
    def structure_must_be_provided_if_populating_from_env_var(
        cls, value: CompleteStructure | None, values: dict
    ) -> CompleteStructure | None:
        if (
            values.get("prepopulate_virtual_structure_adapter_at_designer_startup")
            and not values.get("prepopulate_virtual_structure_adapter_via_file")
            and value is None
        ):
            raise ValueError(
                "structure_to_prepopulate_virtual_structure_adapter must be set "
                "if prepopulate_virtual_structure_adapter_at_designer_startup is set to True "
                "and you want to populate from an environment variable"
            )
        return value

    @validator("structure_to_prepopulate_virtual_structure_adapter")
    def complete_structure_must_not_be_set_if_populating_from_file(
        cls, value: CompleteStructure | None, values: dict
    ) -> CompleteStructure | None:
        if (
            values.get("prepopulate_virtual_structure_adapter_via_file")
            and values.get("structure_filepath_to_prepopulate_virtual_structure_adapter")
            and value is not None
        ):
            raise ValueError(
                "structure_to_prepopulate_virtual_structure_adapter must NOT be set "
                "if prepopulate_virtual_structure_adapter_via_file is set to True, "
                "since you wish to populate from a file"
            )
        return value


environment_file = os.environ.get("HD_VST_ADAPTER_ENVIRONMENT_FILE", None)

vst_adapter_config = VirtualStructureAdapterConfig(
    _env_file=environment_file if environment_file else None  # type: ignore[call-arg]
)


def get_vst_adapter_config() -> VirtualStructureAdapterConfig:
    return vst_adapter_config
