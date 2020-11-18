package org.hetida.designer.backend.dto.engine;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class WorkflowNodeDTO extends BaseNode {
    public List<WorkflowNodeIODTO> inputs = new ArrayList<>();
    public List<WorkflowNodeIODTO> outputs = new ArrayList<>();
    private List<BaseNode> sub_nodes = new ArrayList<>();
    private List<ConnectionDTO> connections = new ArrayList<>();
}
