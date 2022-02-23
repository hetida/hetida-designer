package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.WorkflowExecutionConverter;
import org.hetida.designer.backend.dto.ConfigurationDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionRequestDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.model.Workflow;
import org.hetida.designer.backend.model.WorkflowOperator;
import org.hetida.designer.backend.service.EngineService;
import org.hetida.designer.backend.service.WorkflowExecutionService;
import org.hetida.designer.backend.service.WorkflowService;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@Log4j2
public class WorkflowExecutionServiceImpl implements WorkflowExecutionService {


    private final WorkflowExecutionConverter workflowExecutionConverter;
    private final WorkflowService workflowService;
    private final EngineService engineService;

    public WorkflowExecutionServiceImpl(WorkflowExecutionConverter workflowExecutionConverter, WorkflowService workflowService, EngineService engineService) {
        this.workflowExecutionConverter = workflowExecutionConverter;
        this.workflowService = workflowService;
        this.engineService = engineService;
    }

    @Override
    public ExecutionResponseDTO execute(WiringDTO wiringDTO, UUID workflowId, boolean runPurePlotOperators) {
        return exec(wiringDTO, null, workflowId, runPurePlotOperators);
    }

    @Override
    public ExecutionResponseDTO execute(WiringDTO wiringDTO, ConfigurationDTO configurationDTO, UUID workflowId) {
        return exec(wiringDTO, configurationDTO, workflowId,false);
    }

    private ExecutionResponseDTO exec(WiringDTO wiringDTO, ConfigurationDTO configurationDTO, UUID workflowId,boolean runPurePlotOperators){
        try {
            Workflow workflow = this.workflowService.findById(workflowId);
            List<WorkflowOperator> workflowOperators = this.workflowService.getWorkflowOperatorsRecursive(workflow);
            Map<UUID, Component> allComponents = this.workflowService.getAllComponents(workflowOperators);
            Map<UUID, Workflow> allWorkflows = this.workflowService.getAllWorkflows(workflowOperators);
            allWorkflows.put(workflow.getId(), workflow);

            ExecutionRequestDTO workflowExecutionRequest =
                    this.workflowExecutionConverter.convertExecutionRequestDtoToExecutionRequestDto(
                            wiringDTO, workflowId, allComponents, allWorkflows, runPurePlotOperators);
            if (configurationDTO != null){
                workflowExecutionRequest.setConfiguration(this.workflowExecutionConverter.convertConfigurationDTO(configurationDTO));
            }
            ExecutionResponseDTO workflowExecutionResult = this.engineService.executeWorkflow(workflowExecutionRequest);
            log.debug(workflowExecutionResult.toString());
            return workflowExecutionResult;
        } catch (RuntimeException e) {
            log.error(e.getMessage(), e);
            throw e;
        }
    }


}
