package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
public class WorkflowLinkDTO {
    private UUID id;
    private UUID fromOperator;
    private UUID fromConnector;
    private UUID toOperator;
    private UUID toConnector;
    private List<PointDTO> path = new ArrayList<>();
}
