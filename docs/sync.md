# Sync with local files and hybrid working

The [hdctl](../hdctl) Bash command line tool provides a useful `sync` feature that allows to bidirectionally sync fine-granular selections from a hetida designer instance to a local directory. 

This enables:

* **External version control**: Keep your workflows and components together with the sync config under version control, e.g in a git repository.
* **Edit locally / hybrid working**: Edit / maintain component code locally in an IDE of your choice. Switch frequently between local development and hetida designer user interface.
* **CD/CI and GitOps**: Script deployments between environments (dev => staging => prod)

## Installation
For syncing besides Bash, GNU core utils and curl, [jq](https://jqlang.github.io/jq/) is required. If these preconditions are fulfilled you can just copy the [hdctl script file](../hdctl) to your working environment. 

See the [hdctl script file](../hdctl) for more detailed installation instructions. 

Run `./hdctl usage` for usage details and examples. 

## hdctl sync usage

Sync allows configuration and credentials of the underlying requests against the hetida designer api to reside in local files. In combination with version control, e.g. git,
this enables:

* external version control of workflows/components
* editing locally / hybrid working and frequent switching between local work
and work in the hetida designer user interface
* scripting CD/CI and GitOps

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
recommended to use version control and commit before and after puling and
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

## Frequently used settings

Typically filter settings are configured for pulling only and pushing just pushes everything
available as local file to the hd instance. Let's start with an example in the .hd-instance file

```
PULL_QUERY_URL_APPEND='?include_dependencies=true&include_deprecated=false&id=ec15e0ba-a6f3-4031-8f74-71d33b0b20c6&id=a1230bb-d6f5-2022-ffee-64d33b0b7dee'
```

Here
* `include_dependencies` is set to true. This makes sure every (transitively) dependant component / worklow that is used by the requested workflows is also pulled
* `include_deprecated`` is set to false, which means that deprecated component / workflows are not pulled, even if requested. Note that this does not affect trafos pulled in by `include_dependencies=true`!
* `id=...` is used two times to select 2 transformation revisions by their id. 

The result consists of the two transformation revisions (but not if they are deprecated) plus all their transitive dependencies (regardless of being deprecated or not).

If you want to filter for certain categories you may add `category=Category1&category=Category2`.

Note that filter conditions of different type are combined with logical and.

Other filter conditions are `category_prefix`, `name`, `type`, `state`,  and `revision_group_id`.

There are several other relevant parameters:
* `update_component_code`: Makes sure component code contains correct COMPONENT_INFO and main signature
* `expand_component_code`: Adds documentation and the current test wiring to component code.

Since these options actually edit the component code during export you may be affected by [pitfalls concerning reproducibility and deserializability](./repr_pitfalls.md) when pushing them back or to another instance.

Filter options for pushing are analogous.

Pushing has an additional option `allow_overwrite_released` and also `update_component_code`. You should be especially careful with `allow_overwrite_released` and both these options have the same pitfalls mentioned above!




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

* sync pull && git commit
* make local edits in component code
    * test with local scripts
    * run unit tests contained in component code locally (see below)
* git commit
* sync push
* edit in hd user interface (press control+F5 to reload!), for example:
    * create new revision
    * change io
    * do some test executions
* sync pull && git commit
* ... repeat, then finish your work session with:
* git commit
* sync push


## Run unit tests in component code locally

If component code contains unit tests and a local Python environment ist present with dependencies synced with that of the instance's designer runtime image, one can run all such unit tests using pytest [with appropriate settings for python files](https://docs.pytest.org/en/7.1.x/example/pythoncollection.html#changing-naming-conventions): You must allow pytest to look for tests in all Python files in the export directory.
