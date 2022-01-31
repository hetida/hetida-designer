package org.hetida.designer.backend.dto.engine;

import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class CodeModuleDTO {
    public String code;

    @Column(columnDefinition = "uuid")
    public UUID uuid;

}
