package org.hetida.designer.backend.converter;

import org.hetida.designer.backend.dto.DocumentationDTO;
import org.hetida.designer.backend.model.Documentation;

@org.springframework.stereotype.Component
public class DocumentationConverter {
    public DocumentationDTO convertToDto(Documentation entity) {
        DocumentationDTO dto = new DocumentationDTO();
        dto.setId(entity.getId());
        dto.setDocument(entity.getDocument());
        return dto;
    }

    public Documentation convertToEntity(DocumentationDTO dto) {
        Documentation entity = new Documentation();
        entity.setId(dto.getId());
        entity.setDocument(dto.getDocument());
        return entity;
    }
}
