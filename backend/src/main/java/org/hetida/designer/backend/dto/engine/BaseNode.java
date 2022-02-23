package org.hetida.designer.backend.dto.engine;

import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class BaseNode {
    @Column(columnDefinition = "uuid")
    private UUID id;

}
