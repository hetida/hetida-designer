"""Loading code and importing functions"""
from types import ModuleType
from typing import Callable, Coroutine, Union, Tuple, Optional

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


def module_path_from_code(code: str) -> str:
    """Generates a unique module path from a hash of the actual code"""
    return base_module_path + ".by_code_" + "_hash_" + hash_code(code)


def hash_code(code: str) -> str:
    """Generate a hash from a str representing code that can be used as part of module path"""
    return hex(hash(code)).replace("-", "_m_")


def import_func_from_code(
    code: str,
    func_name: str,
    raise_if_not_found: bool = False,
    register_module: bool = True,
) -> Union[Callable, Coroutine]:
    """Lazily loads a function from the given code and registers the imported module

    The module is only created and registered if direct import does not work. I.e. if the module
    was not created and registered before. This guarantees that the global module code
    is only run once.

    This allows to provide the code of a component dynamically at runtime as a string.
    """

    module_path = module_path_from_code(code)

    try:
        mod = importlib.import_module(module_path)
        func: Union[Callable, Coroutine] = getattr(mod, func_name)
        return func
    except ImportError as e:
        if raise_if_not_found:
            raise e
        logger.info(
            (
                "Function %s from code not yet imported once."
                "Importing it from provided code."
            ),
            func_name,
        )

        mod = ModuleType(module_path)
        if register_module:
            sys.modules[
                module_path
            ] = mod  # now reachable under the constructed module_path
        try:
            # actually import the module;
            exec(code, mod.__dict__)  # pylint: disable=exec-used
        except SyntaxError as exec_syntax_exception:
            logger.info(
                "Syntax Error during importing function %s",
                func_name,
            )
            raise ComponentCodeImportError(
                "Could not import code due to Syntax Errors"
            ) from exec_syntax_exception

        except Exception as exec_exception:
            logger.info(
                "Exception during importing function %s: %s",
                func_name,
                str(exec_exception),
            )
            raise ComponentCodeImportError(
                "Could not import code due to Exception"
            ) from exec_exception

        func = getattr(mod, func_name)
        return func

