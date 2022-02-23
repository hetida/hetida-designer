package org.hetida.designer.backend.listener.kafka.dto;

import lombok.Data;

import java.util.List;

@Data
public class WorkflowWiringDTO {
    private List<InputWiringDTO> input_wirings;
    private List<OutputWiringDTO> output_wirings;
}
