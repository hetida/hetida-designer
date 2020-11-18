package org.hetida.designer.backend.dto;


import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class WorkflowSummaryDTO extends ParentDTO {
    private List<WorkflowIODTO> inputs = new ArrayList<>();
}
