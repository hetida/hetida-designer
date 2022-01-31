package org.hetida.designer.backend.dto.engine;

import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class ConnectionDTO {
    @Column(columnDefinition = "uuid")
    private UUID input_in_workflow_id;

    @Column(columnDefinition = "uuid")
    private UUID input_id;

    private String input_name;

    @Column(columnDefinition = "uuid")
    private UUID output_in_workflow_id;

    @Column(columnDefinition = "uuid")
    private UUID output_id;

    private String output_name;
}
