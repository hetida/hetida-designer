package org.hetida.designer.backend.dto.engine;

import lombok.Data;

import java.util.UUID;

@Data
public class ConnectionDTO {
    private UUID input_in_workflow_id;
    private UUID input_id;
    private String input_name;
    private UUID output_in_workflow_id;
    private UUID output_id;
    private String output_name;
}
