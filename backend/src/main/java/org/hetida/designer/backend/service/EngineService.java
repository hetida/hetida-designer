package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.engine.CodegenRequestDTO;
import org.hetida.designer.backend.dto.engine.ExecutionRequestDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;

public interface EngineService {
    ExecutionResponseDTO executeWorkflow(ExecutionRequestDTO workflowExecutionRequest);
    String generateCode(CodegenRequestDTO codegenRequest);
}
