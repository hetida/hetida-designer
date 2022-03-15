# Tips and Tricks

Since hetida designer is a web application, it is not possible to use the print method to get to the bottom of any errors.
Thus it is recommended to write and test your code, e.g. in a jupyter notebook, before implementing it in components and workflows in hetida designer.

Component as well as workflow revisions can be executed with the test wiring already in the DRAFT state to test if they perform as expected.

Here you can find some guidance for common issues that might occur:

- [Debugging component revisions](#debugging-components)
- [Debugging workflow revisions](#debugging-workflows)
- [Specify data type to enable correct parsing](#data-type-parsing)

## <a name="debugging-components"></a> Debugging component revisions
To understand why and how an error occured it is often necessary to get insights, which variable hat which value at certain steps of running the code.
The only way to achieve this in components is to produce an error message that contains the desired information.
You can raise a ValueError and pass the the variable converted to a string as error message to the ValueError object.

## <a name="debugging-workflows"></a> Debugging workflow revisions
If a workflow does not perform as expected or causes errors, additional information on intermediate variable values might be helpful.
You might want to copy your workflow to have a second version in which you can add and remove operators freely without compromising your actual workflow.
In case of errors you first need to remove the respective component(s) so that the reduced workflow can be executed and all outputs will be displayed.

In order to add an output for an intermediate variable, which is passed from an operator output to some other operators input, add a "Pass through" component with matching data type as operator.
These components are in the category "Connectors".
The output of the "Pass through" operator can be used, to set a new workflow output.

## <a name="data-type-parsing"></a> Specify data type to enable correct parsing