package org.hetida.designer.backend.dto.engine;

import lombok.Data;
import org.hetida.designer.backend.dto.IODTO;

import java.util.Map;
import java.util.UUID;

@Data
public class WorkflowNodeIODTO extends IODTO {
    private UUID id_of_sub_node;
    private String name_in_subnode;
    private boolean constant;
    private Map<String, Object> constantValue;
}
