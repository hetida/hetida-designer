package org.hetida.designer.backend.dto;

import java.util.UUID;

import lombok.Data;

@Data
public class OutputWiringDTO {
    private UUID id;
    private String workflowOutputName;
    private Integer adapterId;
    private String sinkId;
}
