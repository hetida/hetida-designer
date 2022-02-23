package org.hetida.designer.backend.listener.kafka.dto;

import lombok.Data;

@Data
public class ExecutionErrorDTO {
    private String code;
    private String message;
}
