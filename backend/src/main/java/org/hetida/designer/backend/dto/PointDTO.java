package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class PointDTO {
    @Column(columnDefinition = "uuid")
    private UUID id;

    private int posY;
    private int posX;
}
