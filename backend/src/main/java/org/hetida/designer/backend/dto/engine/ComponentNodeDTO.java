package org.hetida.designer.backend.dto.engine;

import lombok.Data;
import org.hetida.designer.backend.dto.IODTO;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import javax.persistence.Column;

@Data
public class ComponentNodeDTO extends BaseNode {
    public List<IODTO> inputs = new ArrayList<>();
    public List<IODTO> outputs = new ArrayList<>();

    @Column(columnDefinition = "uuid")
    private UUID component_uuid;

}
