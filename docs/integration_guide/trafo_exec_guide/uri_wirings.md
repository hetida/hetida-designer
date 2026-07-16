# URI Wirings

## Usage
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
* multiple values for the same filter key will yield a json serialized array
    (i.e. as string) to this filter. This string will then also override any
    value possibly provided with the filters field.
* `ref_key` and `ref_id_type` and `attrs` can be provided in the "fragment" part of the uri, if necessary

E.g, an input wiring that uses the pass through int component via the component adapter can be specified via

```json
{
    "uri": "hd://component-adapter/57eea09f-d28e-89af-4e81-2027697a3f0f?input=55",
    "workflow_input_name": "input",
}
```

## Uri Wiring Shortcuts
Configuratively you can specify shortcuts via `HETIDA_DESIGNER_URI_WIRING_SHORTCUTS` environment variable, for both backend and runtime service. This is a dict pointing to pairs of adapter id and ref id of a source. E.g.

```
{"assets": ["component-adapter", "<id of some component adapter source component>"]}
```

allows to use uri wirings of form `hd://assets?recursive=true` as a shortcut for the full `hd://component-adapter/<id of some component adapter source component>?recursive=true`.

Furthermore it allows to configuratively upgrade/change such wirings by simply changing it to pointing to another component adapter source id. Note: Doing this may negatively impact reproducibility if configuration changes are not carefully taken into account when trying to reproduce results.

### Uri Wiring shortcuts in hetida platform
Using [hetida platform](https://hetida.io/), typically the following wiring shortcuts are configured:

* `hd://assets` — points to the hetida platform source component "Hetida Platform Assets" that provides assets as a dataframe at the current point in the hierarchy.
* `hd://timeseries` — points to the hetida platform source component "Hetida Platform Channel Timeseries Data" that provides dynamic collections of timeseries data at and below the current asset as a multitsframe.