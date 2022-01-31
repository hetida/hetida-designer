package org.hetida.designer.backend.dto;

import lombok.Data;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.enums.ItemType;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class ParentDTO {

    @Column(columnDefinition = "uuid")
    private UUID id;

    @Column(columnDefinition = "uuid")
    private UUID groupId;

    private String name;
    private String description;
    private String category;
    private ItemType type;
    private ItemState state;
    private String tag;
}
