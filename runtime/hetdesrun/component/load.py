"""Loading code and importing functions"""

import datetime
import hashlib
import importlib
import logging
import sys
from collections.abc import Callable, Coroutine
from types import ModuleType
from uuid import UUID, uuid4

from hetdesrun.component.base_module import base_module_path
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import ComponentRevision
from hetdesrun.runtime.logging import execution_context_filter


class ComponentCodeImportError(Exception):
    """Component Code could not be imported"""


class ComponentImportCycleError(ComponentCodeImportError):
    """Cycle detected during component import"""


logger = logging.getLogger(__name__)


def module_path_from_code_hash(code_hash: str) -> str:
    """Generates a unique module path from a precomputed code hash"""
    return base_module_path + ".by_code_" + "_hash_" + code_hash


def module_path_from_code(code: str) -> str:
    """Generates a unique module path from a hash of the actual code"""
    return module_path_from_code_hash(hash_code(code))


def get_module_path(code_module: CodeModule) -> str:
    """Obtain unique module path using possibly cached code hash

    If the code was already hashed in this execution's context than
    this avoids recomputation of the hash.
    """
    return module_path_from_code_hash(get_code_hash(code_module))


def code_hash_from_execution_context_binding(trafo_id: UUID) -> str | None:
    """Obtains code hash from execution context

    returns None if code hash is not registered in the
    execution context.
    """

    code_hash_dict: dict[str, str] | None = execution_context_filter.get_value("code_hash_dict")
    if code_hash_dict is None:
        return None

    assert code_hash_dict is not None  # for mypy # noqa: S101

    return code_hash_dict.get(str(trafo_id))


def get_code_hash(
    code_module: CodeModule, register_in_execution_context_if_computing: bool = True
) -> str:
    """Get code hash, computing it if necessary

    If code hash is already registered in execution context for the trafo id,
    obtain it from there. If not: compute it.

    If register_in_execution_context_if_computing is True, then the computed hash
    is registered in the execution context. This de facto caches the code hash in
    the context of the current execution.
    """

    possible_code_hash: str | None = code_hash_from_execution_context_binding(code_module.uuid)

    if possible_code_hash is None:
        code_hash = hash_code(code_module.code)
        if register_in_execution_context_if_computing:
            code_hash_dict = execution_context_filter.get_value("code_hash_dict")
            if code_hash_dict is None:
                code_hash_dict = {}
                execution_context_filter.bind_context(code_hash_dict=code_hash_dict)
            code_hash_dict[str(code_module.uuid)] = code_hash

        return code_hash

    assert possible_code_hash is not None  # for mypy # noqa: S101
    return possible_code_hash


def hash_code(code: str) -> str:
    """Generate a hash from a str representing code that can be used as part of module path"""
    return hashlib.sha256(code.encode("utf8")).hexdigest()


def import_comp(trafo_id: str) -> ModuleType:
    """Actually import another component code module from within component code

    This expects the respective target CodeModule and ComponentRevision to be
    present in the runtime execution context, as should be done by the prepare
    runtime context bindings step.
    """

    component_revisions_by_trafo_id = execution_context_filter.get_value(
        "component_revisions_by_trafo_id"
    )
    if component_revisions_by_trafo_id is None:
        component_revisions_by_trafo_id = {}

    if trafo_id not in component_revisions_by_trafo_id:
        raise ComponentCodeImportError(f"Missing component revision for id {trafo_id}")

    component_revision = component_revisions_by_trafo_id[trafo_id]

    code_module_uuid = str(component_revision.code_module_uuid)

    code_modules_by_id = execution_context_filter.get_value("code_modules_by_id")
    if code_modules_by_id is None:
        code_modules_by_id = {}

    if code_module_uuid not in code_modules_by_id:
        raise ComponentCodeImportError(f"Missing component code module for id {code_module_uuid}")

    code_module = code_modules_by_id[code_module_uuid]

    return import_from_code_module(code_module, component_revision)


def import_from_code_module(
    code_module: CodeModule,
    component_revision: ComponentRevision,
    raise_if_not_found: bool = False,
    register_module: bool = True,
) -> ModuleType:
    """Lazily loads a module from the given code module and registers the imported module

    This allows to provide the code of a component dynamically at runtime as a string.

    The module is only created and registered if direct import does not work. I.e. if the module
    was not created and registered before. This guarantees that the global module code
    is only run once.

    Detects cycles when from within the component code other component modules are imported
    via a mechanism that itself uses this function. E.g. via import_comp.
    """
    module_path = get_module_path(code_module)  # cached, via hash from code

    currently_importing = execution_context_filter.get_value("currently_importing")

    if currently_importing is None:
        currently_importing = {}
        execution_context_filter.bind_context(currently_importing=currently_importing)

    if currently_importing.get(code_module.uuid, False):
        msg = (
            "Component import cycle detected while running import_from_code_module"
            f" for component with id {code_module.uuid}"
        )
        logger.error(msg)
        raise ComponentImportCycleError(msg)

    currently_importing[code_module.uuid] = True

    try:
        # try to import existing
        mod = importlib.import_module(module_path)
    except ImportError as e:  # probably not found at module_path
        if raise_if_not_found:
            raise e

        import_start = datetime.datetime.now(tz=datetime.timezone.utc)

        mod = ModuleType(module_path)

        mod_display_filename_for_tracebacks = (
            f"CODE OF COMPONENT {component_revision.name}"
            f" ({component_revision.tag}) UUID {component_revision.uuid}"
        )
        try:
            # actually import the module;
            compiled_code = compile(
                code_module.code, filename=mod_display_filename_for_tracebacks, mode="exec"
            )
            exec(compiled_code, mod.__dict__)  # noqa: S102 # nosec B102
        except SyntaxError as exec_syntax_exception:
            logger.info(
                "Syntax Error during importing code module (%s (%s), uuid: %s)",
                component_revision.name,
                component_revision.tag,
                component_revision.uuid,
            )
            raise ComponentCodeImportError(
                "Could not import code due to Syntax Errors"
            ) from exec_syntax_exception

        except Exception as exec_exception:  # noqa: BLE001
            logger.info(
                "Exception during importing code module (%s (%s), uuid: %s): %s",
                component_revision.name,
                component_revision.tag,
                component_revision.uuid,
                str(exec_exception),
            )
            raise ComponentCodeImportError(
                f"Could not import code due to Exception {str(exec_exception)}"
            ) from exec_exception

        if register_module:
            sys.modules[module_path] = mod  # now reachable under the constructed module_path

        logger.debug(
            (
                "Code module for (%s (%s), uuid: %s) was not yet imported once. "
                "Importing it from provided code under module path %s took %s."
            ),
            component_revision.name,
            component_revision.tag,
            component_revision.uuid,
            module_path,
            datetime.datetime.now(tz=datetime.timezone.utc) - import_start,
        )
    finally:
        currently_importing[code_module.uuid] = False

    return mod


def import_func_from_code_module(
    func_name: str,
    code_module: CodeModule,
    component_revision: ComponentRevision,
    raise_if_not_found: bool = False,
    register_module: bool = True,
) -> Callable | Coroutine:
    """Load a single global function object from a component code module by its name

    Relies on import_from_code_module and provides the same guarantees.
    """

    mod = import_from_code_module(
        code_module=code_module,
        component_revision=component_revision,
        raise_if_not_found=raise_if_not_found,
        register_module=register_module,
    )

    func: Callable | Coroutine = getattr(mod, func_name)

    return func


def import_func_from_code_wrapper(
    code: str, func_name: str, raise_if_not_found: bool = False, register_module: bool = True
) -> Callable | Coroutine:
    """Wrapper to import directly from code string

    Uses / generates stub CodeModule and ComponentRevision objects.

    Helpful for testing.
    """
    common_uuid = uuid4()
    code_module = CodeModule(code=code, uuid=common_uuid)
    comp_rev = ComponentRevision(
        name="WRAPPER",
        uuid=common_uuid,
        tag="UNKNOWN",
        code_module_uuid=common_uuid,
        function_name=func_name,
        inputs=[],
        outputs=[],
    )
    return import_func_from_code_module(
        func_name,
        code_module,
        comp_rev,
        raise_if_not_found=raise_if_not_found,
        register_module=register_module,
    )
