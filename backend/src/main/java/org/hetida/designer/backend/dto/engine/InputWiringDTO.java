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
    private Integer adapterId;
    @JsonProperty("source_id")
    private String sourceId;
    @JsonInclude()
    private Map<String, Object> filters = new HashMap<>();
}
