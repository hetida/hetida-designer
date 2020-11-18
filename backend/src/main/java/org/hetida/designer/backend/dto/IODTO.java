package org.hetida.designer.backend.dto;

import lombok.Data;
import org.hetida.designer.backend.enums.IOType;

import java.util.UUID;

@Data
public class IODTO {

    private UUID id;
    private IOType type;
    private String name;
    private int posY;
    private int posX;

}
