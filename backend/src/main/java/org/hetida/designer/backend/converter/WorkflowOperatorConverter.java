package org.hetida.designer.backend.converter;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.WorkflowOperatorDTO;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.exception.ComponentNotFoundException;
import org.hetida.designer.backend.exception.WorkflowNotFoundException;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.model.Workflow;
import org.hetida.designer.backend.model.WorkflowOperator;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@org.springframework.stereotype.Component
@Log4j2
public class WorkflowOperatorConverter {

    private final IOConverter IOConverter;

    public WorkflowOperatorConverter(org.hetida.designer.backend.converter.IOConverter IOConverter) {
        this.IOConverter = IOConverter;
    }

    public List<WorkflowOperatorDTO> convertToOperatorDtos(final List<WorkflowOperator> entities, Map<UUID, org.hetida.designer.backend.model.Component> allComponents, Map<UUID, Workflow> allWorkflows) {

        List<WorkflowOperatorDTO> operators = new ArrayList<>();
        if (entities != null) {
            for (WorkflowOperator workflowOperator : entities) {
                operators.add(this.convertToOperatorDto(workflowOperator, allComponents, allWorkflows));
            }
        }
        return operators;


    }

    public List<WorkflowOperator> convertToOperatorEntities(final List<WorkflowOperatorDTO> dtos) {
        return dtos == null ? null : dtos.stream()
                .map(this::convertToOperatorEntity)
                .collect(Collectors.toList());
    }

    private WorkflowOperatorDTO convertToOperatorDto(WorkflowOperator entity, Map<UUID, Component> allComponents, Map<UUID, Workflow> allWorkflows) {
        WorkflowOperatorDTO operatorDTO = new WorkflowOperatorDTO();
        operatorDTO.setId(entity.getId());
        operatorDTO.setItemId(entity.getItemId());
        operatorDTO.setName(entity.getName());
        operatorDTO.setType(entity.getType());
        operatorDTO.setPosX(entity.getPosX());
        operatorDTO.setPosY(entity.getPosY());


        if (ItemType.COMPONENT.equals(entity.getType())) {
            if (!allComponents.containsKey(entity.getItemId())) {
                throw new ComponentNotFoundException();
            }
            org.hetida.designer.backend.model.Component component = allComponents.get(entity.getItemId());
            operatorDTO.setTag(component.getTag());
            operatorDTO.setDescription(component.getDescription());
            operatorDTO.setCategory(component.getCategory());
            operatorDTO.setGroupId(component.getGroupId());
            operatorDTO.setState(component.getState());
            operatorDTO.setInputs(this.IOConverter.convertComponentIOToIODtos(component.getInputs()));
            operatorDTO.setOutputs(this.IOConverter.convertComponentIOToIODtos(component.getOutputs()));
        } else {
            if (!allWorkflows.containsKey(entity.getItemId())) {
                throw new WorkflowNotFoundException();
            }
            Workflow workflow = allWorkflows.get(entity.getItemId());
            operatorDTO.setTag(workflow.getTag());
            operatorDTO.setDescription(workflow.getDescription());
            operatorDTO.setCategory(workflow.getCategory());
            operatorDTO.setGroupId(workflow.getGroupId());
            operatorDTO.setState(workflow.getState());
            operatorDTO.setInputs(this.IOConverter.convertWorkflowIOToOperatorIODtos(workflow.getInputs()));
            operatorDTO.setOutputs(this.IOConverter.convertWorkflowIOToOperatorIODtos(workflow.getOutputs()));

        }
        return operatorDTO;
    }

    private WorkflowOperator convertToOperatorEntity(WorkflowOperatorDTO dto) {
        WorkflowOperator workflowOperator = new WorkflowOperator();
        workflowOperator.setId(dto.getId());
        workflowOperator.setItemId(dto.getItemId());
        workflowOperator.setName(dto.getName());
        workflowOperator.setType(dto.getType());
        workflowOperator.setPosX(dto.getPosX());
        workflowOperator.setPosY(dto.getPosY());

        return workflowOperator;
    }
}
