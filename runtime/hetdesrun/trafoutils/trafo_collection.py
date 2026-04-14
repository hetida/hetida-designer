import logging
from types import TracebackType
from uuid import UUID

from hetdesrun.exportimport.importing import TrafoUpdateProcessSummary, import_importable
from hetdesrun.persistence.models.transformation import (
    TransformationRevision,
)
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.load import (
    Importable,
    ImportSourceConfig,
    MultipleTrafosUpdateConfig,
    load_json,
    transformation_revision_from_python_code,
)

logger = logging.getLogger(__name__)


class TrafoCollection:
    """Context Manager helping collecting transformation revisions

    This can be used for
    * workflow construction: collect necessary operator trafos
    * unit tests: flexibly collect trafos from different sort of files, db etc. and store
      them in db.
    """

    def __init__(self, save_to_db: bool = False, store_into_directory: str | None = None):
        self.save_to_db = save_to_db
        self.store_into_directory = store_into_directory
        self.registered_trafos: list[TransformationRevision] = []

    def __enter__(self: TrafoCollection) -> TrafoCollection:
        return self

    def __exit__(
        self: TrafoCollection,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.save_to_db:
            self._save_to_db()
        if self.store_into_directory:
            self._store_into_directory()

    def add(self, trafo: TransformationRevision) -> TransformationRevision:
        self.registered_trafos.append(trafo)
        return trafo

    def add_from_code(self, code: str) -> TransformationRevision:
        return self.add(transformation_revision_from_python_code(code))

    def add_from_py_file(self, path: str) -> TransformationRevision:
        with open(path) as f:
            code = f.read()

        return self.add_from_code(code)

    def add_from_json_file(self, path: str) -> TransformationRevision:
        tr_json = load_json(path)
        return self.add(TransformationRevision(**tr_json))

    def add_path(self, path: str) -> TransformationRevision:
        if path.endswith(".py"):
            return self.add_from_py_file(path)
        if path.endswith(".json"):
            return self.add_from_json_file(path)

        raise ValueError(
            f"Trafo Collection add_path got file path with unknown file extension: {path}"
        )

    def _save_to_db(self) -> dict[UUID | str, TrafoUpdateProcessSummary]:
        # TODO: expose more options from FilterParams or MultipleTrafosUpdateConfig?
        importable = Importable(
            transformation_revisions=self.registered_trafos,
            import_config=ImportSourceConfig(
                filter_params=FilterParams(), update_config=MultipleTrafosUpdateConfig()
            ),
        )

        success_per_trafo = import_importable(importable)
        logger.info("Result of Trafo Collection saving:\n%s", success_per_trafo)
        return success_per_trafo

    def _store_into_directory(self) -> None:
        raise NotImplementedError
