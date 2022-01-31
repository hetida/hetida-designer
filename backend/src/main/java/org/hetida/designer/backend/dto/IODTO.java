package org.hetida.designer.backend.dto;

import lombok.Data;
import org.hetida.designer.backend.enums.IOType;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class IODTO {

    @Column(columnDefinition = "uuid")
    private UUID id;

    private IOType type;
    private String name;
    private int posY;
    private int posX;

}
