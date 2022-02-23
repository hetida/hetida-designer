package org.hetida.designer.backend.dto.engine;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

@Data
public class WorkflowWiringDTO {
    @JsonProperty("input_wirings")
    private List<InputWiringDTO> inputWirings;
    @JsonProperty("output_wirings")
    private List<OutputWiringDTO> outputWirings;
}
