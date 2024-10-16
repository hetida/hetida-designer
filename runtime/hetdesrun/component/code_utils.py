"""Utils for code parsing and transforming using black, ast and libcst

We use libcst (https://libcst.readthedocs.io) for code manipulation
instead of Python's builtin ast capabilities because we want to produce
and preserve readable source code. E.g. we want to keep comments, newlines
etc.
"""

import ast
from typing import Any

import black
import libcst as cst
import libcst.matchers as m


class CodeParsingException(Exception):
    pass


class LiteralEvalError(CodeParsingException):
    pass


def format_code_with_black(code: str) -> str:
    """Format code with black

    Raises CodeParsingException if there are SyntaxErrors in the code.
    """
    # based on https://stackoverflow.com/a/76052629
    # `format_file_contents`currently best candidate to become the official Python API according to
    # https://github.com/psf/black/issues/779
    try:
        code = black.format_file_contents(
            code,
            fast=False,
            mode=black.Mode(
                target_versions={black.TargetVersion.PY312},  # python3.12
            ),
        )
    except black.NothingChanged:
        pass
    except black.InvalidInput as exc:
        msg = f"Could not format code with black: {str(exc)}"
        raise CodeParsingException(msg) from exc
    finally:
        # Make sure there's a newline after the content
        if len(code) != 0 and code[-1] != "\n":
            code += "\n"
    return code


def get_module_doc_string(code: str) -> str | None:
    """Extracts docstring from module code

    Returns None if there is no module docstring.
    """
    try:
        parsed_cst = cst.parse_module(code)
    except cst.ParserSyntaxError as exc:
        msg = f"Could not extract module docstring - failed parsing code: {str(exc)}"
        raise CodeParsingException(msg) from exc

    return parsed_cst.get_docstring()


def get_global_from_code(code: str, variable_name: str, default_value: Any = None) -> Any:
    """Extracts content from a global assignment in the provided code

    Using ast.literal_eval allows to store metadata directly in Python code
    and extract it from there securly, see
    https://stackoverflow.com/questions/15197673/using-pythons-eval-vs-ast-literal-eval

    * The assignment must be a single target assignment
    * it must be on the highest code level
    * The value is parsed using ast.literal_eval,
      see (https://docs.python.org/3/library/ast.html#ast.literal_eval)
      for the restrictions coming from that.

    Returns the provided default_value if nothing is found.

    Raises CodeParsingException or LiteralEvalError.
    """
    try:
        parsed_ast = ast.parse(code)
    except (SyntaxError, ValueError) as exc:
        msg = f"Could not parse provided Python Code into AST. Error was: {str(exc)}"
        raise CodeParsingException(msg) from exc

    for element in parsed_ast.body:
        if isinstance(element, ast.Assign):
            if len(element.targets) != 1:  # only consider single target assignments
                continue
            assign_target = element.targets[0]

            if not hasattr(assign_target, "id"):
                continue

            if assign_target.id == variable_name:  # type: ignore
                try:
                    return ast.literal_eval(element.value)
                except (
                    ValueError,
                    TypeError,
                    SyntaxError,
                    MemoryError,
                    RecursionError,
                ) as exc:
                    msg = (
                        f"Could not literal_eval the assignment value for {variable_name}. "
                        f"Error was: {str(exc)}"
                    )
                    raise LiteralEvalError(msg) from exc
    # not found
    return default_value


def cst_from_python_value(value: Any, format_with_black: bool = False) -> cst.BaseExpression:
    """Get CST representation for a constant Python expression

    libcst hast no Constant class like ast.

    In ast one would use ast.Constant(value=value).

    Of course a naive approach is to use
        cst.parse_expression(repr(value))

    but that depends too much on repr implementation for the given object being
    complete and actually representative of the object construction.

    So we take an additional step through code combining ast.Constant,
    ast.unparse and cst.parse_expression.
    """

    try:
        constant_code = ast.unparse(ast.Constant(value=value))
    except RecursionError as exc:
        msg = f"The expression {value} is too complex and cannot be unparsed."
        raise LiteralEvalError(msg) from exc
    if format_with_black:
        return cst.parse_expression(format_code_with_black(constant_code))
    return cst.parse_expression(constant_code)


class GlobalAssignValueTransformer(cst.CSTTransformer):
    """Add/Update the value of a module-level variable assignment

    If not present, the assignment will be added to the module's end.

    This can be used to store and update information in a Python code module
    in a module-level variable.
    """

    def __init__(
        self,
        variable_name: str,
        value: Any,
        replace_all: bool = False,
        remove_repetitions: bool = True,
    ):
        self.variable_name = variable_name
        self.value = value
        self.found_once = False
        self.replace_all = replace_all

        # If True, and not replace_all: Keep only first Assignment statement.
        self.remove_repetitions = remove_repetitions

        self.assigns: set = set()

    def visit_Module(self, node: cst.Module) -> None:
        gathered_assigns = []
        for element in node.body:
            if m.matches(element, m.SimpleStatementLine()):
                for stmt in cst.ensure_type(element, cst.SimpleStatementLine).body:
                    if m.matches(
                        stmt,
                        m.Assign(targets=[m.AssignTarget(target=m.Name(value=self.variable_name))]),
                    ):
                        gathered_assigns.append(stmt)
        self.assigns = set(gathered_assigns)

    def leave_Module(
        self,
        original_node: cst.Module,  # noqa: ARG002
        updated_node: cst.Module,
    ) -> cst.Module:
        if not self.found_once:
            # append to module
            module_body = list(updated_node.body)
            module_body.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.Assign(
                            targets=[cst.AssignTarget(target=cst.Name(value=self.variable_name))],
                            value=cst_from_python_value(self.value, format_with_black=True),
                        )
                    ]
                )
            )
            return updated_node.with_changes(body=module_body)
        return updated_node

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.Assign | cst.RemovalSentinel:
        # replace value only on module level!

        # TODO: Removing here is only allowed to happen if left name assignment
        #       is correct. This needs to be checked here as well!

        if not original_node in self.assigns:
            return updated_node

        if len(original_node.targets) != 1:
            return updated_node

        if self.found_once and not self.replace_all:
            if self.remove_repetitions:
                return cst.RemoveFromParent()
            return updated_node

        assign_target = original_node.targets[0]  # cst.AssignTarget
        assign_target_target = assign_target.target  # cst.Name

        if assign_target_target.value == self.variable_name:  # type: ignore
            self.found_once = True
            return updated_node.with_changes(
                # Instead of value = ast.literal_eval({"99": 98.7})
                value=cst_from_python_value(self.value, format_with_black=True)
            )

        return updated_node


def update_module_level_variable(code: str, variable_name: str, value: Any) -> str:
    """Updates or adds the module-level variable"""

    try:
        parsed_cst = cst.parse_module(code)
    except cst.ParserSyntaxError as exc:
        msg = f"Failure parsing code module using cst: {str(exc)}"
        raise CodeParsingException(msg) from exc

    transformer = GlobalAssignValueTransformer(variable_name, value)

    try:
        new_cst = parsed_cst.visit(transformer)
    except (
        cst.ParserSyntaxError,
        CodeParsingException,
    ) as exc:
        msg = f"Failure updating code: {str(exc)}"
        raise CodeParsingException(msg) from exc

    return new_cst.code
