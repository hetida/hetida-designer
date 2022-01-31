package org.hetida.designer.backend.model;

import lombok.Data;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import java.util.UUID;

@Entity
@Data
@Table(name = "point")
public class Point {
    @Id
    @Column(name = "id", columnDefinition = "uuid")
    private UUID id;

    @Column(name = "posy")
    private int posY;

    @Column(name = "posx")
    private int posX;

    @Column(name = "sequencenr")
    private int sequenceNr;
}
