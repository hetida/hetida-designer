package org.hetida.designer.backend.dto;


import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class DocumentationDTO {
    @Column(columnDefinition = "uuid")
    private UUID id;

    private String document;
}
