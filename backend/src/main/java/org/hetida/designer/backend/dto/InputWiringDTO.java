package org.hetida.designer.backend.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.util.Map;
import java.util.UUID;

@Data
public class InputWiringDTO {
    private UUID id;
    private String workflowInputName;
    private String adapterId;
    private String refId;
    private String refIdType;
    private String refKey;
    private String type;
    @JsonInclude()
    private Map<String, String> filters; 
    private String value;
}
