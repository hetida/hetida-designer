package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class OutputWiringDTO {
    @Column(columnDefinition = "uuid")
    private UUID id;

    private String workflowOutputName;
    private String adapterId;
    private String refId;
    private String refIdType;
    private String refKey;
    private String type;
}
