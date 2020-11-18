package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.Map;
import java.util.UUID;

@Data
public class WorkflowIODTO extends IODTO {
    private UUID operator;
    private UUID connector;
    private boolean constant;
    private Map<String, Object> constantValue;
}
