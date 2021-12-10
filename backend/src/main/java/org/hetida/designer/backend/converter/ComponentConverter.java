package org.hetida.designer.backend.converter;

import org.hetida.designer.backend.dto.ComponentDTO;
import org.hetida.designer.backend.dto.engine.CodegenRequestDTO;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.model.Component;

import java.util.stream.Collectors;

@org.springframework.stereotype.Component
public class ComponentConverter {

    private final IOConverter IOConverter;
    private final WorkflowWiringConverter wiringConverter;

    public ComponentConverter(org.hetida.designer.backend.converter.IOConverter IOConverter, WorkflowWiringConverter workflowWiringConverter) {
        this.IOConverter = IOConverter;
        this.wiringConverter = workflowWiringConverter;
    }

    public ComponentDTO convertToDto(Component entity) {
        ComponentDTO componentDTO = new ComponentDTO();
        componentDTO.setCategory(entity.getCategory());
        componentDTO.setDescription(entity.getDescription());
        componentDTO.setGroupId(entity.getGroupId());
        componentDTO.setId(entity.getId());
        componentDTO.setName(entity.getName());
        componentDTO.setState(entity.getState());
        componentDTO.setTag(entity.getTag());
        componentDTO.setCode(entity.getCode());
        componentDTO.setType(ItemType.COMPONENT);
        componentDTO.setInputs(this.IOConverter.convertComponentIOToIODtos(entity.getInputs()));
        componentDTO.setOutputs(this.IOConverter.convertComponentIOToIODtos(entity.getOutputs()));
        componentDTO.setWirings(entity.getWirings().stream().map(this.wiringConverter::toWiringDto).collect(Collectors.toList()));

        return componentDTO;
    }

    public Component convertToEntity(ComponentDTO componentDto) {
        Component component = new Component();
        component.setCategory(componentDto.getCategory());
        component.setDescription(componentDto.getDescription());
        component.setGroupId(componentDto.getGroupId());
        component.setId(componentDto.getId());
        component.setName(componentDto.getName());
        component.setState(componentDto.getState());
        component.setTag(componentDto.getTag());
        component.setCode(componentDto.getCode());
        component.setInputs(this.IOConverter.convertToComponentIOEntities(componentDto.getInputs()));
        component.setOutputs(this.IOConverter.convertToComponentIOEntities(componentDto.getOutputs()));
        if (componentDto.getWirings() != null){
            component.setWirings(componentDto.getWirings().stream().map(this.wiringConverter::toWiring).collect(Collectors.toList()));
        }
        return component;
    }

    public CodegenRequestDTO convertToCodegenRequestDto(Component entity) {
        CodegenRequestDTO codegenRequestDTO = new CodegenRequestDTO();
        codegenRequestDTO.setCode(entity.getCode());
        codegenRequestDTO.setInputs(this.IOConverter.convertComponentIOToIODtos(entity.getInputs()));
        codegenRequestDTO.setOutputs(this.IOConverter.convertComponentIOToIODtos(entity.getOutputs()));
        codegenRequestDTO.setName(entity.getName());
        codegenRequestDTO.setDescription(entity.getDescription());
        codegenRequestDTO.setCategory(entity.getCategory());
        codegenRequestDTO.setUuid(entity.getId());
        codegenRequestDTO.setGroup_id(entity.getGroupId());
        codegenRequestDTO.setTag(entity.getTag());
        return codegenRequestDTO;
    }

}
