package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.UUID;

@Data
public class PointDTO {
    private UUID id;
    private int posY;
    private int posX;
}
