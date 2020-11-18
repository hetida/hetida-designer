"""Loading code and importing functions"""
from types import ModuleType
from typing import Callable, Coroutine, Union, Tuple, Optional

from uuid import UUID

import sys
import logging
import importlib


class ComponentCodeImportError(Exception):
    """Component Code could not be imported"""


logger = logging.getLogger(__name__)


base_module_path = "hetdesrun_loaded_components"
# Register base_module_path. This is necessary in order for serialization
# to work with custom classes in user components.
#
# Note: As long as base_module_path is not configurable and only has one
# level we do not need to recursively register modules:
sys.modules[base_module_path] = ModuleType(base_module_path, "base module")


def module_path_from_uuid_and_code(uuid: UUID, code: str) -> str:
    """Generates a unique module path from uuid and a hash of the actual code"""
    return (
        base_module_path
        + ".by_uuid_"
        + str(uuid).replace("-", "_")
        + "_hash_"
        + hash_code(code)
    )


def hash_code(code: str) -> str:
    """Generate a hash from a str representing code that can be used as part of module path"""
    return hex(hash(code)).replace("-", "_m_")


def import_func_from_code(
    code: str, uuid: UUID, func_name: str, register_module: bool = True
) -> Union[Callable, Coroutine]:
    """Imports function from provided code

    Allows to register code as a new module at a module path whic is
    generated from uuid and code.
    """
    module_path = module_path_from_uuid_and_code(uuid, code)

    mod = ModuleType(module_path, "module that was loaded automatically")
    # pylint: disable=exec-used

    if register_module:
        sys.modules[
            module_path
        ] = mod  # now reachable under the constructed module_path

    try:
        exec(code, mod.__dict__)  # actually import the module.
    except SyntaxError as e:
        logger.info(
            "Syntax Error during importing function %s with code module id %s",
            func_name,
            str(uuid),
        )
        raise ComponentCodeImportError(
            "Could not import code due to Syntax Errors"
        ) from e

    except Exception as e:
        logger.info(
            "Exception during importing function %s with code module id %s: %s",
            func_name,
            str(uuid),
            str(e),
        )
        raise ComponentCodeImportError("Could not import code due to Exception") from e

    func: Union[Coroutine, Callable] = getattr(mod, func_name)
    return func


def import_func_from_code_with_uuid_as_modulename(
    code: str, uuid: UUID, func_name: str, raise_if_not_found: bool = False
) -> Union[Coroutine, Callable]:
    """Lazily loads a function from the given code and registers the imported module

    The module is only created and registered if direct import does not work. I.e. if the module
    was not created and registered before. This guarantees that the global module code
    is only run once.

    This allows to provide the code of a component dynamically at runtime as a string.
    """

    module_path = module_path_from_uuid_and_code(uuid, code)
    try:
        mod = importlib.import_module(module_path)
        func: Union[Callable, Coroutine] = getattr(mod, func_name)
        return func
    except ImportError as e:
        if raise_if_not_found:
            raise e
        logger.info(
            (
                "Function %s from code with code module uuid %s not yet imported once. "
                "Importing it from provided code."
            ),
            func_name,
            str(uuid),
        )
        return import_func_from_code(code, uuid, func_name, register_module=True)


def check_importability(code: str, func_name: str) -> Tuple[bool, Optional[Exception]]:
    """Very simple check just to see whether the code is at least importable"""
    try:
        import_func_from_code(
            code,
            UUID("97d1433a-f739-4190-aaed-4bd846b7cf20"),
            func_name,
            register_module=False,
        )
        return True, None
    except Exception as e:  # pylint: disable=broad-except
        return False, e
