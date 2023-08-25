## <a name="using-default-values"></a> Using Default Values

The hetida designer provides the possibility to define default values for input parameters. To do this, first open the dialog for configuring inputs and outputs.

<img src="./assets/optional_input.png" height="110" width=645 data-align="center">

Change the input type from "REQUIRED" to "DEFAULT", then the input field for the default values appears.

<img src="./assets/default_value.png" height="110" width=645 data-align="center">

Not entering a value will result in the default value `None`, also for inputs of type `STRING`. To obtain an empty string as default value, enter a string and remove it with the backspace key.

Optional inputs are not displayed in the preview (or at an operator) by default, but a grey bar with a white triangle in the center pointing down indicates the presence of hidden optional inputs.
Thus, the display becomes clearer.

For components, the code is updated accordingly after saving the changes so that the actual default value is clear.

<img src="./assets/code_with_default_value.png" height="290" width=380 data-align="center">

For the convenience of the user, optional inputs are wired to their default value by default and are displayed greyed out in the input filed. Toggling the toggle switch will change the adapter to "manual input" and make the value editable.

<img src="./assets/wire_to_default_value.png" height="85" width=625 data-align="center">

To overwrite the default value of an optional operator input in a workflow, the respective input must be exposed.

<img src="./assets/wire_to_untoggled_default_value.png" height="85" width=625 data-align="center">

Clicking on the grey bar opens a pop-up window in which all optional inputs are displayed with their default values and can be exposed or hidden by ticking or unticking them.

<img src="./assets/expose_dialog.png" height="105" width=395 data-align="center">

A white border around the operator input indicates that it is an optional input that can be hidden if desired.
Just like component inputs, workflow inputs can be made optional, which is also indicated by a white border around the workflow input. As expected in such a case, the outer default value overwrites the inner default value.

<img src="./assets/exposed_input_with_optional_wf_input.png" height="105" width=395 data-align="center">
