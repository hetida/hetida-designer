package org.hetida.designer.backend.listener.kafka.dto;


import lombok.Data;

import java.util.UUID;

@Data
public class WiredExecutionDTO {
    private UUID workflowId;
    private WorkflowWiringDTO workflow_wiring;
    private ConfigurationDTO configuration;

}
