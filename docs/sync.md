# Sync with local files and hybrid working

The [hdctl](../hdctl) Bash command line tool provides a useful `sync` feature that allows to sync fine-granular selections from a hetida designer instance to a local directory and vice-versa.

This enables:

* **External version control**: Keep your workflows and components together with the sync config under version control, e.g in a git repository.
* **Edit locally / hybrid working**: Edit / maintain component code locally in an IDE of your choice. Switch frequently between local development and hetida designer user interface.
* **CD/CI and GitOps**: Script deployments between environments (dev => staging => prod)

## Installation
For syncing besides Bash, GNU core utils and curl, [jq](https://jqlang.github.io/jq/) is required. If these preconditions are fulfilled you can just copy the [hdctl script file](../hdctl) to your working environment.

See the [hdctl script file](../hdctl) for more detailed installation instructions.

Run `./hdctl usage` for usage details and examples.

## hdctl sync usage

Sync allows configuration and credentials of the underlying requests against the hetida designer api to reside in local files.

The configuration and credential files for a remote hetida designer instance
you want to name "my-hd-instance" can be pregenerated via

```
hdctl sync init my-hd-instance
```

Make sure you follow the instructions this command prints out! After that
you should have at least a `my-hd-instance.hd-instance` file and a
`my-hd-instance.hd-creds` file which are used as configuration for syncing.


Additionally a `my-hd-instance.hd-creds.stub` file is present that can be checked into
version control together with the .hd-instance file. You should of course never
put the `my-hd-instance.hd-creds` into version control since you have entered actual passwords and secrets there. Put `*.hd-creds` into your `.gitignore` instead!

You can now transfer transformations from/to the configured local directory via

```
hdctl sync pull my-hd-instance
hdctl sync push my-hd-instance
```

Note that pulling overwrites the local directory completely.
> It is strongly
recommended to use version control and commit before and after pulling and
pushing.

Note that what is pulled and pushed depends on the settings in your .hd-instance
file. The query url parameters of the `/api/transformations` GET and PUT endpoints
allow for fine-granular filtering and updating / expanding the exported
component code with documentation and a wiring. See below for more information on often-used parameters!

Sync of the local file content of my-hd-instance to/from another configured
instance named my-other-hd-instance can be done via

```
hdctl sync push my-other-hd-instance from my-hd-instance
hdctl sync pull my-other-hd-instance to my-hd-instance
```

This pushes / pulls with the settings of my-other-hd-instance but uses the
export directory configured for my-hd-instance as source / target.

## Frequently used parameters and settings

Typically filter settings are configured for pulling only and pushing just pushes everything
available as local file to the hd instance. Let's start with an example in the .hd-instance file

```
PULL_QUERY_URL_APPEND='?include_dependencies=true&include_deprecated=false&id=ec15e0ba-a6f3-4031-8f74-71d33b0b20c6&id=a1230bb-d6f5-2022-ffee-64d33b0b7dee'
```

Here
* `include_dependencies` is set to true. This makes sure every (transitively) dependant component / worklow that is used by the requested workflows is also pulled
* `include_deprecated` is set to false, which means that deprecated component / workflows are not pulled, even if requested. Note that this does not affect trafos pulled in by `include_dependencies=true`!
* `id=...` is used two times to select 2 transformation revisions by their id.

The result consists of the two transformation revisions (but not if they are deprecated) plus all their transitive dependencies (regardless of being deprecated or not).

If you want to filter for certain categories you may add `category=Category1&category=Category2`.

Note that filter conditions of different type are combined with logical AND and filter conditions of the same kind are combined with OR.

Other filters are `category_prefix`, `name`, `type`, `state`,  and `revision_group_id`.

`include_dependencies` is recommended
* for backups
* for transfering to other instances to guarantee that all dependencies are included

`include_dependencies` is not necessary for hybrid  working on component code.

There are several other relevant parameters:
* `update_component_code`: Makes sure component code contains correct COMPONENT_INFO and main signature
* `expand_component_code`: Adds documentation and the current test wiring to component code.

Since these options actually edit the component code during export you may be affected by [pitfalls concerning reproducibility and deserializability](./repr_pitfalls.md) when pushing them back or to another instance.

Filter options for pushing are analogous.

Pushing has an additional option `allow_overwrite_released` and also `update_component_code`. You should be especially careful with `allow_overwrite_released` and both these options have the same pitfalls mentioned above!

Let's describe some typical combinations of settings by providing examples:

### Hybrid working on a component draft
To work safely on draft components. See below for details on hybrid working. Allows to add inputs or outputs directly in the `COMPONENT_INFO`
part of the code or change the description there.

```
EXPORT_COMPONENTS_AS_PY_FILES=true

PULL_QUERY_URL_APPEND='?id=ec15e0c4-a6f3-4031-8f74-71d33b0420c6&update_component_code=true&expand_component_code=true'
PUSH_QUERY_URL_APPEND='?allow_overwrite_released=false&update_component_code=true'
```

### Hybrid working on a released component
See below for details on hybrid working.
> **Warning:** Overwriting released components is dangerous: For example it may destroy workflows depending on them! In particular if inputs or ouputs are added/removed. It circumvents reproducibility.

```
EXPORT_COMPONENTS_AS_PY_FILES=true

PULL_QUERY_URL_APPEND='?id=ec15e0c3-a6f3-4031-8f74-71223b0b20c6&update_component_code=true&expand_component_code=true'
PUSH_QUERY_URL_APPEND='?allow_overwrite_released=true&update_component_code=true'
```

### Backup
The example backups two categories and all their dependencies when pulling. Note that pushing (i.e. restoring the backup) is allowed to overwrite released transformations.
```
EXPORT_COMPONENTS_AS_PY_FILES=false # export everything as json file

PULL_QUERY_URL_APPEND='?category=Smoothing&category=Preparation&include_dependencies=true&update_component_code=false&expand_component_code=false'
PUSH_QUERY_URL_APPEND='?allow_overwrite_released=true&update_component_code=false'
```

To backup everything on your instance simply remove all filters (here both category filters).

Restore is done via pushing.

### Transfer between instances
You need 2 instances, lets call them `staging` and `prod`. Settings are basically the same as for backup for both instances. You can then use a hdctl sync subcommand feature for transfering, which comes in two variants:

```
hdctl sync pull staging

# recommended: git commit before pushing

# pushes from local directory of staging to the prod instance
hdctl sync push prod from staging
```
or
```
# pull from staging but save in local directory of prod
hdctl sync pull staging to prod

# recommended: git commit before pushing

hdctl push prod
```

You also can specify the export directory that should be used directly using the `-d` command line parameter:

```
hdctl sync push prod -d /path/to/trafo/directory
```


## Hybrid working using sync features
"hybrid working" means editing components both via the hetida designer user interface and as local files and switching frequently between both editing "modes".

### Working hybrid recommendations
* Set filter parameters for `sync pull` to only sync the subset of components/workflows to what you actually want to edit. For example only certain categories:

```
PULL_QUERY_URL_APPEND=?include_dependencies=true&include_deprecated=false&category=Timeseries
```

* Avoid possibly destructive sync settings (like `overwrite_released` for pushing, see below for more details). Instead create new draft revisions in the user interface, pull and edit them locally, push and release them via user interface.
* Use git! Always git commit before pushing and after pulling in order to be able to restore if something bad happens.
* Solve conflicts locally — using git features if necessary.
* Sync regurlarly and finish your work session with a push.

#### Recommended hybrid working workflow

* `sync pull` and `git commit`
* make local edits in component code
    * test with local scripts
    * run unit tests contained in component code locally (see below)
* `git commit` and `sync push`
* edit in hd user interface (press control+F5 to reload!), for example:
    * create new revision
    * change io
    * do some test executions
* `sync pull` and `git commit`
* ... repeat, then finish your work session with:
* `git commit` and `sync push`


### Run unit tests in component code locally

If component code contains unit tests and a local Python environment ist present with dependencies synced with that of the instance's designer runtime image, one can run all such unit tests using pytest: To accomplish this, hdctl sync automatically creates an [appropriate](https://docs.pytest.org/en/7.1.x/example/pythoncollection.html#changing-naming-conventions) pytest.ini file in the export directory. This pytest.ini file also activates detection and running of [doctests](https://docs.python.org/3/library/doctest.html).

#### Writing unit tests

Unit tests should be entered directly in your component code files, for example as functions prefixed with `test_`.

For example entering the following function at the bottom of a component which contains a `TEST_WIRING_FROM_PY_FILE_IMPORT` will create a test that runs the component's main function with those input wirings which are `direct_provisioning` data.

```py
from hdutils import parse_value  # noqa: E402


def test_run_with_test_wiring():
    result = main(
        **{
            inp_wiring["workflow_input_name"]: parse_value(
                inp_wiring["filters"]["value"],
                COMPONENT_INFO["inputs"][inp_wiring["workflow_input_name"]][
                    "data_type"
                ],
                nullable=True,
            )
            for inp_wiring in TEST_WIRING_FROM_PY_FILE_IMPORT["input_wirings"]
            if inp_wiring.get("adapter_id", "direct_provisioning")  == "direct_provisioning"
        }
    )

    assert isinstance(result, dict)
    ...
```

If you need to import pytest, e.g. to use one of its decorators or `pytest.raises` we recommend to put all your tests in the `else` part of a try ... except ... else block around the pytest import as follows:

```python
...
# bottom of component code

try:
    import pytest
except ImportError:
    pass
else:
    @pytest.mark.parametrize("test_str", ["test1", "test2"])
    def test_one(test_str):
        assert main(test_str=test_str) == test_str

    def test_two():
        with pytest.raises(ValueError):
            main(test_str="error")
```

This guarantees that
* your component code will run in the runtime container where only prod dependencies are installed meaning that pytest typically is not available.
* during running the unit tests in an environment with dev dependencies installed you can use all features of pytest.

#### Writing doctests
You can enter doctests as [usual](https://docs.python.org/3/library/doctest.html) in your functions docstring. For the component's main function the docstring must be entered below the comment marking the end of the auto-generated function header:
```py
...
def main(...)
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    """Are doctests working?
    >>> 2 + 3
    5
    """
```

#### Running all unit tests and doctests
To execute all unit tests run
```
python -m pytest .
```
in the export directory. This command should be run from a Python environment with the runtime dev dependencies installed.
