# URI Wirings
Input / output wirings can alternatively specified via only `workflow_input_name` (or `workflow_output_name`) and a `uri` field.

If such a uri is provided, its information
will override other wiring fields. The uri's filters (via query params) will update
and supplement filters provided via the filters field, possibly overwriting
them. I.e. filters set by uri have higher precedence.

The format is

    hd://<adapter_key>/<ref_id>?filter_key_1=filter_value_1&other_filter=other_value#ref_key=<ref_key>&ref_id_type=<ref_id_type>

Notes on uri:
* Schema must be "hd"
* must be properly url encoded
* multiple values for the same filter key will yield an json serialized array
    (i.e. a string) to this filter. This string will then also override any
    value possibly provided with the filters field.
* `ref_key` and `ref_id_type` and `attrs` can be provided in the "fragment" part of the uri, if necessary

E.g, an input wiring that uses the pass through int component via the component adapter can be specified via

```json
{
    "uri": "hd://component-adapter/57eea09f-d28e-89af-4e81-2027697a3f0f?input=55",
    "workflow_input_name": "input",
}
```