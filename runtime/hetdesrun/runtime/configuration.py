"""Configuration of workflow execution

This is used to inject execution configuration information into
the entrypoint registration decorator.
"""

from contextvars import ContextVar

from hetdesrun.models.run import ConfigurationInput

execution_config: ContextVar[ConfigurationInput] = ContextVar(
    "execution_configuration", default=ConfigurationInput()
)
