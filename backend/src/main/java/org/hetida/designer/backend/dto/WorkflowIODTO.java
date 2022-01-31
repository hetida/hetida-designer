package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.Map;
import java.util.UUID;

import javax.persistence.Column;

@Data
public class WorkflowIODTO extends IODTO {
    @Column(columnDefinition = "uuid")
    private UUID operator;

    @Column(columnDefinition = "uuid")
    private UUID connector;

    private boolean constant;
    private Map<String, Object> constantValue;
}
