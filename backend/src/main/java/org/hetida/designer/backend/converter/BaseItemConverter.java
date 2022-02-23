package org.hetida.designer.backend.converter;

import org.hetida.designer.backend.dto.BaseItemDTO;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.model.Workflow;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class BaseItemConverter {
    private final WorkflowWiringConverter wiringConverter;
    private final IOConverter ioConverter;

    public BaseItemConverter(IOConverter ioConverter, WorkflowWiringConverter workflowWiringConverter) {
        this.ioConverter = ioConverter;
        this.wiringConverter = workflowWiringConverter;
    }

    public BaseItemDTO convertComponentToDto(org.hetida.designer.backend.model.Component entity) {
        BaseItemDTO baseItemDTO = new BaseItemDTO();
        baseItemDTO.setCategory(entity.getCategory());
        baseItemDTO.setDescription(entity.getDescription());
        baseItemDTO.setGroupId(entity.getGroupId());
        baseItemDTO.setId(entity.getId());
        baseItemDTO.setName(entity.getName());
        baseItemDTO.setState(entity.getState());
        baseItemDTO.setTag(entity.getTag());
        baseItemDTO.setInputs(this.ioConverter.convertComponentIOToIODtos(entity.getInputs()));
        baseItemDTO.setOutputs(this.ioConverter.convertComponentIOToIODtos(entity.getOutputs()));
        baseItemDTO.setWirings(entity.getWirings().stream().map(this.wiringConverter::toWiringDto).collect(Collectors.toList()));
        baseItemDTO.setType(ItemType.COMPONENT);
        return baseItemDTO;
    }

    public final List<BaseItemDTO> convertComponentsToDtos(final List<org.hetida.designer.backend.model.Component> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertComponentToDto)
                .collect(Collectors.toList());
    }

    public BaseItemDTO convertWorkflowToDto(org.hetida.designer.backend.model.Workflow entity) {
        BaseItemDTO baseItemDTO = new BaseItemDTO();
        baseItemDTO.setCategory(entity.getCategory());
        baseItemDTO.setDescription(entity.getDescription());
        baseItemDTO.setGroupId(entity.getGroupId());
        baseItemDTO.setId(entity.getId());
        baseItemDTO.setName(entity.getName());
        baseItemDTO.setState(entity.getState());
        baseItemDTO.setTag(entity.getTag());
        baseItemDTO.setInputs(this.ioConverter.convertWorkflowIOToIODtos(entity.getInputs()));
        baseItemDTO.setOutputs(this.ioConverter.convertWorkflowIOToIODtos(entity.getOutputs()));
        baseItemDTO.setWirings(entity.getWirings().stream().map(this.wiringConverter::toWiringDto).collect(Collectors.toList()));
        baseItemDTO.setType(ItemType.WORKFLOW);
        return baseItemDTO;
    }


    public final List<BaseItemDTO> convertWorkflowsToDtos(final List<org.hetida.designer.backend.model.Workflow> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertWorkflowToDto)
                .collect(Collectors.toList());
    }

    public org.hetida.designer.backend.model.Component convertToComponentEntity(BaseItemDTO componentDto) {
        org.hetida.designer.backend.model.Component component = new org.hetida.designer.backend.model.Component();
        component.setCategory(componentDto.getCategory());
        component.setDescription(componentDto.getDescription());
        component.setGroupId(componentDto.getGroupId());
        component.setId(componentDto.getId());
        component.setName(componentDto.getName());
        component.setState(componentDto.getState());
        component.setTag(componentDto.getTag());
        return component;
    }

    public Workflow convertToWorkflowEntity(BaseItemDTO workflowDto) {
        Workflow workflow = new Workflow();
        workflow.setCategory(workflowDto.getCategory());
        workflow.setDescription(workflowDto.getDescription());
        workflow.setGroupId(workflowDto.getGroupId());
        workflow.setId(workflowDto.getId());
        workflow.setName(workflowDto.getName());
        workflow.setState(workflowDto.getState());
        workflow.setTag(workflowDto.getTag());
        return workflow;
    }

    public org.hetida.designer.backend.model.Component mergeToComponentEntity(BaseItemDTO componentDto, org.hetida.designer.backend.model.Component component) {
        component.setCategory(componentDto.getCategory());
        component.setDescription(componentDto.getDescription());
        component.setGroupId(componentDto.getGroupId());
        component.setId(componentDto.getId());
        component.setName(componentDto.getName());
        component.setState(componentDto.getState());
        component.setTag(componentDto.getTag());
        component.setInputs(this.ioConverter.convertToComponentIOEntities(componentDto.getInputs()));
        component.setOutputs(this.ioConverter.convertToComponentIOEntities(componentDto.getOutputs()));
        return component;
    }

    public Workflow mergeToWorkflowEntity(BaseItemDTO workflowDto, Workflow workflow) {
        workflow.setCategory(workflowDto.getCategory());
        workflow.setDescription(workflowDto.getDescription());
        workflow.setGroupId(workflowDto.getGroupId());
        workflow.setId(workflowDto.getId());
        workflow.setName(workflowDto.getName());
        workflow.setState(workflowDto.getState());
        workflow.setTag(workflowDto.getTag());
        return workflow;
    }
}
