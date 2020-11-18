package org.hetida.designer.backend.model;


import lombok.Data;
import org.hetida.designer.backend.enums.ItemType;

import javax.persistence.*;
import java.util.UUID;

@Entity
@Data
@Table(name = "workflowoperator")
public class WorkflowOperator {

    @Id
    @Column(name = "id")
    private UUID id;

    @Column(name = "itemid")
    private UUID ItemId;

    @Column(name = "name")
    private String name;

    @Column(name = "type")
    @Enumerated(EnumType.STRING)
    private ItemType type;

    @Column(name = "posy")
    private int posY;

    @Column(name = "posx")
    private int posX;
}




