package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.WorkflowExecutionConverter;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionRequestDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.service.ComponentExecutionService;
import org.hetida.designer.backend.service.ComponentService;
import org.hetida.designer.backend.service.EngineService;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@Log4j2
public class ComponentExecutionServiceImpl implements ComponentExecutionService {

    private final WorkflowExecutionConverter workflowExecutionConverter;
    private final ComponentService componentService;
    private final EngineService engineService;

    public ComponentExecutionServiceImpl(WorkflowExecutionConverter workflowExecutionConverter, ComponentService componentService, EngineService engineService) {
        this.workflowExecutionConverter = workflowExecutionConverter;
        this.componentService = componentService;
        this.engineService = engineService;
    }

    @Override
    public ExecutionResponseDTO execute(WiringDTO wiringDTO, UUID componentId, boolean runPurePlotOperators) {
        try {
            Component component = this.componentService.findById(componentId);
            ExecutionRequestDTO workflowExecutionRequest = this.workflowExecutionConverter.convertComponentExecutionRequestDtoToExecutionRequestDto(wiringDTO, component, runPurePlotOperators);
            ExecutionResponseDTO workflowExecutionResult = this.engineService.executeWorkflow(workflowExecutionRequest);
            log.debug(workflowExecutionResult.toString());
            return workflowExecutionResult;
        } catch (RuntimeException e) {
            log.error(e.getMessage(), e);
            throw e;
        }
    }
}
