package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.ConfigurationDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;

import java.util.UUID;

public interface WorkflowExecutionService {
    ExecutionResponseDTO execute(WiringDTO wiringDTO, UUID workflowId, boolean runPurePlotOperators);
    ExecutionResponseDTO execute(WiringDTO wiringDTO, ConfigurationDTO configurationDTO, UUID workflowId);
}
