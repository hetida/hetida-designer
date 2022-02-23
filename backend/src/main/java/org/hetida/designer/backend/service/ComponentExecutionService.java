package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;

import java.util.UUID;

public interface ComponentExecutionService {
    ExecutionResponseDTO execute(WiringDTO componentExecutionDTO, UUID componentId, boolean runPurePlotOperators);
}
