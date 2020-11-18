package org.hetida.designer.backend.dto;


import lombok.Data;

import java.util.UUID;

@Data
public class DocumentationDTO {
    private UUID id;
    private String document;
}
