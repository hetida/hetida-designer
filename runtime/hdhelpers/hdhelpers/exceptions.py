from typing import Any


class HelperException(Exception):
    """Exception to re-raise exceptions with error code raised in the code of the hdhelpers
    package."""

    __is_hetida_designer_exception__ = True

    def __init__(
        self,
        *args: Any,
        error_code: int | str = "",
        extra_information: dict | None = None,
        **kwargs: Any,
    ) -> None:
        if not isinstance(error_code, int | str):
            raise ValueError("The HelperException.error_code must be int or string!")
        self.error_code = error_code
        self.extra_information = extra_information
        super().__init__(*args, **kwargs)
