# Component writing tips

Components are the base artefacts of hetida designer.


## Logging
Logging should be used as usual with the help of the standard library:

```python
import logging
logger = logging.getLogger(__name__)
# ...
def main(...):
    # ...
    logger.info("Log message")
```

During execution log messages from inside components emitted this way are captured and
returned as part of the execution result. In hetida designer execution result view these
log messages are displayed.

## Debugging

`print(...)` and setting breakpoints will not work for debugging, since component code is run remotely.

You can use logging instead as described above for basic debugging purposes. Or you can raise an exception containing relevant debugging information in its message.

## Unit tests

Components can contain unit tests (pytest) directly in their component code, i.e.
functions prefixed with `test_`. Doctests are also supported.

Unit tests can be run from the designer user interface using the corresponding symbol bar button at the top of the corresponding component editor tab.

## Importing other components

It is possible to import other components and use functions / classes etc from them:

```python
from hetdesrun.component.load import import_comp
# refer to other component by its id:
my_other_component = import_comp("abcdef12-4567-890a-bcde-f1234567890a")
func_from_other = my_other_component.func_from_other

# ...
def main(...):
    # ...
    func_from_other(...)
    # ...
```

You can obtain another component's id by opening its "Edit component details" dialogue (pencil icon) in hetida designer.

If the id is valid, you can hover over it in the code to see its name and version and you can ctrl+click on it to access the imported component.

Note that for releasing, all imported components must also be released.

Note also that import_comp must be called in a global assignment statement for this to work.





