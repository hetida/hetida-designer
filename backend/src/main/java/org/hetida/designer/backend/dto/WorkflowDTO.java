package org.hetida.designer.backend.dto;


import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class WorkflowDTO extends ParentDTO {
    public List<WorkflowOperatorDTO> operators = new ArrayList<>();
    public List<WorkflowLinkDTO> links = new ArrayList<>();
    private List<WorkflowIODTO> inputs = new ArrayList<>();
    private List<WorkflowIODTO> outputs = new ArrayList<>();
    private List<WiringDTO> wirings;
}
