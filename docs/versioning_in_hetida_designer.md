# hetida designer component and workflow versioning

hetida designer comes with a versioning system for both components and workflows. For example when creating a component you have to provide a version tag and you are actually creating a new revision of the component (its first revision in this case).

For both workflows and components what you are actually working on is always a revision! Generally in hetida designer's documentation we often omit the term "revision" when talking about components or workflows in order to simplify the documentation language a bit. For example the entries in the sidebar for both components and workflows always include the version tag and when you double click on such an entry you actually open this revision. But we may simply say "open the component" in the documentation instead.

## Revisions for components
### DRAFT Mode
A new component revision starts its existence in "DRAFT" mode which means it can be edited, i.e. inputs/outputs can be changed and the source code can be modified freely. On the other side "DRAFT" mode means that this component revision cannot be dragged into a workflow. This limitation is necessary in order to guarantee reproducibility and stability of workflow execution in production setups. For being able to use your component in workflows it needs to be published.

### Publishing (Releasing) and Updating
A revision in DRAFT mode can be published via the appropriate button in the UI. After publishing the component revision's mode is now "RELEASED". This means it cannot be edited anymore (neither source code nor inputs/outputs) but can now be dragged into and used in workflows.

If later you need to change the component you have to create a new revision for this component through the UI button for "new revision" in the component view. Again you have to provide a version tag for this new revision of your component and it starts in DRAFT mode.

Note that even when publishing this new second revision of your component the instances of your first revision in existing workflows won't be updated automatically! This protects working workflows from unexpected changes in their behaviour and again this is necessary to guarantee stability and reproducibility of workflow execution. Instead you have to manually update your workflows and replace the old revision with the new one. However there is a mechanism supporting you which is called "deprecation".

### Deprecating revisions
You can deprecate a revision of a component that you do not want to be used anymore (probably because there exists a newer, better revision of this component). To do so you have to press the deprecate button in the component revision's view and confirm this step. After that this component revision is not deleted — instead it is marked as deprecated which has the following consequences:

* The deprecated revision does not occur in the component sidebar anymore. It therefore cannot be dragged into workflows which prevents new uses of it.
* In every workflow where instances of this component revision are used, they are marked as deprecated. If the workflow itself can be edited (i.e. is in DRAFT mode) you can rightclick on such an instance and choose to replace it with another (probably newer) revision. This will replace the instance. At the moment this does not try to keep connections from/to this instance so you probably need to replace them manually. Trying to keep connections is a feature we plan to add at a later time.
* All workflows with deprecated component revision instances will still work as before. In particular note that workflow revisions which itself are RELEASED cannot be changed even through deprecating. Instead you need to create a new revision for the workflow itself in this case.

Note again: Deprecated revisions are never deleted, they are still present in the hetida designer database and this guarantees that old versions of workflows will execute as before.

### Copying a component revision
To create a new component from an existing component you can open one of its revisions and press the copy button. This creates a first revision for a completely new component starting with the same IO and source code but otherwise having no relations to the old component (and its revisions). In particular revisions of this new component cannot be chosen when replacing a deprecated revision of the old component from the rightclick-dialog on the deprecated instance in a workflow and so on.


## Revisions for workflows
Workflows also have revisions and they work completely the same as with the components. There is DRAFT state in which workflow revisions are editable and a RELEASED state where they are fixed and cannot be edited anymore. Note that workflow revisions itself can be dragged into workflows and then behave like a component instance (i.e. nesting workflows is possible and encouraged!). This can only be done if the workflow revision that is dragged is published (in RELEASE mode) and of course the target workflow must be editable (hence in DRAFT mode).

Also deprecating and updating workflow revision instances works the same way and copying workflows is completely analogous.

## A note on version tags
The hetida designer does not require the tags to follow any particular pattern. They are simply identifiers for the different revisions and can be used similarly to Docker image tags. You are free to use more meaningful strings than version numbers. Just note that the tags must be short (20 characters maximum) and unique within the revision group.