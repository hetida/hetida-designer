package org.hetida.designer.backend.dto.engine;

import lombok.Data;
import org.hetida.designer.backend.dto.IODTO;

import java.util.Map;
import java.util.UUID;

import javax.persistence.Column;

@Data
public class WorkflowNodeIODTO extends IODTO {
    @Column(columnDefinition = "uuid")
    private UUID id_of_sub_node;

    private String name_in_subnode;
    private boolean constant;
    private Map<String, Object> constantValue;
}
