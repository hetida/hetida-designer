package org.hetida.designer.backend.converter;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.WorkflowLinkDTO;
import org.hetida.designer.backend.model.WorkflowLink;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
@Log4j2
public class WorkflowLinkConverter {

    private final PointConverter pointConverter;

    public WorkflowLinkConverter(PointConverter pointConverter) {
        this.pointConverter = pointConverter;
    }

    public List<WorkflowLink> convertToLinkEntities(final List<WorkflowLinkDTO> dtos) {
        return dtos == null ? null : dtos.stream()
                .map(this::convertToLinkEntity)
                .collect(Collectors.toList());
    }

    public List<WorkflowLinkDTO> convertToLinkDtos(final List<WorkflowLink> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertToLinkDto)
                .collect(Collectors.toList());
    }

    private WorkflowLink convertToLinkEntity(WorkflowLinkDTO dto) {
        WorkflowLink link = new WorkflowLink();
        link.setId(dto.getId());
        link.setFromOperator(dto.getFromOperator());
        link.setFromConnector(dto.getFromConnector());
        link.setToOperator(dto.getToOperator());
        link.setToConnector(dto.getToConnector());
        link.setPath(this.pointConverter.convertToPointEntities(dto.getPath()));
        return link;
    }

    private WorkflowLinkDTO convertToLinkDto(WorkflowLink entity) {
        WorkflowLinkDTO linkDTO = new WorkflowLinkDTO();
        linkDTO.setId(entity.getId());
        linkDTO.setFromOperator(entity.getFromOperator());
        linkDTO.setFromConnector(entity.getFromConnector());
        linkDTO.setToOperator(entity.getToOperator());
        linkDTO.setToConnector(entity.getToConnector());
        linkDTO.setPath(this.pointConverter.convertToPointDtos(entity.getPath()));
        return linkDTO;
    }
}
