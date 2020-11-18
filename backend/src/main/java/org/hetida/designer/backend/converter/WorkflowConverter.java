package org.hetida.designer.backend.converter;

import org.hetida.designer.backend.dto.WorkflowDTO;
import org.hetida.designer.backend.dto.WorkflowSummaryDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.model.Workflow;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Component
public class WorkflowConverter {
    private final IOConverter IOConverter;
    private final WorkflowLinkConverter workflowLinkConverter;
    private final WorkflowOperatorConverter workflowOperatorConverter;
    private final WorkflowWiringConverter workflowWiringConverter;

    public WorkflowConverter(org.hetida.designer.backend.converter.IOConverter IOConverter, WorkflowLinkConverter workflowLinkConverter, WorkflowOperatorConverter workflowOperatorConverter, WorkflowWiringConverter workflowWiringConverter) {
        this.IOConverter = IOConverter;
        this.workflowLinkConverter = workflowLinkConverter;
        this.workflowOperatorConverter = workflowOperatorConverter;
        this.workflowWiringConverter = workflowWiringConverter;
    }

    public WorkflowDTO convertToDto(Workflow entity, Map<UUID,  org.hetida.designer.backend.model.Component> allComponents, Map<UUID, Workflow> allWorkflows) {
        WorkflowDTO workflowDTO = new WorkflowDTO();
        workflowDTO.setCategory(entity.getCategory());
        workflowDTO.setDescription(entity.getDescription());
        workflowDTO.setGroupId(entity.getGroupId());
        workflowDTO.setId(entity.getId());
        workflowDTO.setName(entity.getName());
        workflowDTO.setState(entity.getState());
        workflowDTO.setTag(entity.getTag());
        workflowDTO.setType(ItemType.WORKFLOW);
        workflowDTO.setLinks(this.workflowLinkConverter.convertToLinkDtos(entity.getLinks()));
        workflowDTO.setOperators(this.workflowOperatorConverter.convertToOperatorDtos(entity.getWorkflowOperators(), allComponents, allWorkflows));
        workflowDTO.setInputs(this.IOConverter.convertWorkflowIOToWorkflowIODTOs(entity.getInputs()));
        workflowDTO.setOutputs(this.IOConverter.convertWorkflowIOToWorkflowIODTOs(entity.getOutputs()));

        List<WiringDTO> wiringDTO = entity.getWirings().stream().map(this.workflowWiringConverter::toWiringDto).collect(Collectors.toList());
        workflowDTO.setWirings(wiringDTO);

        return workflowDTO;
    }


    public Workflow convertToEntity(WorkflowDTO workflowDto) {
        Workflow workflow = new Workflow();
        workflow.setCategory(workflowDto.getCategory());
        workflow.setDescription(workflowDto.getDescription());
        workflow.setGroupId(workflowDto.getGroupId());
        workflow.setId(workflowDto.getId());
        workflow.setName(workflowDto.getName());
        workflow.setState(workflowDto.getState());
        workflow.setTag(workflowDto.getTag());
        workflow.setLinks(this.workflowLinkConverter.convertToLinkEntities(workflowDto.getLinks()));
        workflow.setWorkflowOperators(this.workflowOperatorConverter.convertToOperatorEntities(workflowDto.getOperators()));
        workflow.setInputs(this.IOConverter.convertWorkflowIODTOToEntities(workflowDto.getInputs()));
        workflow.setOutputs(this.IOConverter.convertWorkflowIODTOToEntities(workflowDto.getOutputs()));
        if (workflowDto.getWirings() != null){
            workflow.setWirings(workflowDto.getWirings().stream().map(this.workflowWiringConverter::toWiring).collect(Collectors.toList()));
        }
        return workflow;
    }

    public WorkflowSummaryDTO convertToSummaryDto(Workflow workflow){
        WorkflowSummaryDTO summaryDTO = new WorkflowSummaryDTO();
        summaryDTO.setId(workflow.getId());
        summaryDTO.setGroupId(workflow.getGroupId());
        summaryDTO.setName(workflow.getName());
        summaryDTO.setDescription(workflow.getDescription());
        summaryDTO.setCategory(workflow.getCategory());
        summaryDTO.setState(workflow.getState());
        summaryDTO.setTag(workflow.getTag());
        summaryDTO.setType(ItemType.WORKFLOW);
        summaryDTO.setInputs(this.IOConverter.convertWorkflowIOToWorkflowIODTOs(workflow.getInputs()));
        return summaryDTO;
    }


}
