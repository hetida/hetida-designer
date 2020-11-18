package org.hetida.designer.backend.listener.kafka.dto;

import lombok.Data;

import java.util.Map;

@Data
public class InputWiringDTO {
    private String workflow_input_name;
    private Integer adapter_id;
    private String source_id;
    private Map<String, String> filters;
}
