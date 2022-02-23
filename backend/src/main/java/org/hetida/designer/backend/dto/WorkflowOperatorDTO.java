package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import javax.persistence.Column;

@Data
public class WorkflowOperatorDTO extends ParentDTO {
    @Column(columnDefinition = "uuid")
    public UUID itemId;

    private List<IODTO> inputs = new ArrayList<>();
    private List<IODTO> outputs = new ArrayList<>();
    private int posY;
    private int posX;
}
