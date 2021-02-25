package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.UUID;

@Data
public class OutputWiringDTO {
    private UUID id;
    private String workflowOutputName;
    private String adapterId;
    private String refId;
    private String refIdType;
    private String refKey;
    private String type;
}
