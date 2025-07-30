# Logging in the hetida designer

This article covers logging in the hetida designer codebase.  
For information on reading execution logs and logging in component code refer to this [article](execution/logging.md).

## Logging setup

The hetida designer produces structured logs, using [structlog](https://www.structlog.org).  
Logging is set up so that both standard library and structlog-native logging can be used.  
Log records are passed through a processor chain, defined in this [file](../runtime/hetdesrun/__init__.py).

## Usage

### Standard library logging

The usual way to log using the standard library can be used:
```python
import logging

logger = logging.getLogger(__name__) 
logger.info("hetida designer is awesome!")
```
Behind the scenes, the log record this code produces, is transformed to a JSON log entry. Only this processed entry will show up in the logs.  
You can attach extra information in the form of key-value pairs to the log record as follows:
```python
logger.info("hetida designer is awesome!", extra={"important_number": 42})
```
This could be any information, as long as it can be parsed into a JSON.  
The data passed via `extra` is appended to the final log entry as an additional JSON field.
As long as the key is part of the whitelist defined by the environment variable `CUSTOM_ATTRIBUTES_TO_LOG`.

### Structlog logging

Structlog-native logs can be produced as follows:
```python
import structlog
logger = structlog.get_logger()
logger.info(
    "hetida designer is awesome!",  # Event message
    user=username,                  # Optional key-value pair
    source_ip=ip_address            # Another optional key-value pair
)
```
The information you pass via the key-value pairs will be appended to the final log entry as an additional JSON field.
When using structlog, this does not require the keys to be whitelisted.