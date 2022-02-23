package org.hetida.designer.backend.listener.kafka.dto;


import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class WiredExecutionDTO {
    @Column(columnDefinition = "uuid")
    private UUID workflowId;

    private WorkflowWiringDTO workflow_wiring;
    private ConfigurationDTO configuration;

}
