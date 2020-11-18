package org.hetida.designer.backend.dto.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class OutputWiringDTO {
    @JsonProperty("workflow_output_name")
    private String workflowOutputName;
    @JsonProperty("adapter_id")
    private Integer adapterId;
    @JsonProperty("sink_id")
    private String sinkId;
}
