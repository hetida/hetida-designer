package org.hetida.designer.backend.dto.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class OutputWiringDTO {

    @JsonProperty("workflow_output_name")
    private String workflowOutputName;

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
}
