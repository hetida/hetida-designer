package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import javax.persistence.Column;

@Data
public class WorkflowLinkDTO {
    @Column(columnDefinition = "uuid")
    private UUID id;

    @Column(columnDefinition = "uuid")
    private UUID fromOperator;

    @Column(columnDefinition = "uuid")
    private UUID fromConnector;

    @Column(columnDefinition = "uuid")
    private UUID toOperator;

    @Column(columnDefinition = "uuid")
    private UUID toConnector;

    private List<PointDTO> path = new ArrayList<>();
}
