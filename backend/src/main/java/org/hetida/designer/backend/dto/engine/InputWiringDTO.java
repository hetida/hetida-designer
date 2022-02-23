package org.hetida.designer.backend.dto.engine;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.HashMap;
import java.util.Map;

@Data
public class InputWiringDTO {

    @JsonProperty("workflow_input_name")
    private String workflowInputName;

    @JsonProperty("adapter_id")
    private String adapterId;

    @JsonProperty("ref_id")
    private String refId;

    @JsonProperty("ref_id_type")
    private String refIdType;

    @JsonProperty("ref_key")
    private String refKey;

    @JsonProperty("type")
    private String type;

    @JsonInclude()
    private Map<String, Object> filters = new HashMap<>();
}
