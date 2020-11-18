package org.hetida.designer.backend.model;

import lombok.Data;
import org.hetida.designer.backend.enums.IOType;

import javax.persistence.*;
import java.util.UUID;

@Data
@MappedSuperclass
public class BaseIO {
    @Id
    @Column(name = "id")
    private UUID id;

    @Column(name = "type")
    @Enumerated(EnumType.STRING)
    private IOType type;

    @Column(name = "name")
    private String name;

    @Column(name = "posy")
    private int posY;

    @Column(name = "posx")
    private int posX;
}
