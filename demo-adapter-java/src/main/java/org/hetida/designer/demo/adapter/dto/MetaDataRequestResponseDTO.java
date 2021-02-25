package org.hetida.designer.demo.adapter.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
public class MetaDataRequestResponseDTO {
    private String key;
    private Object value;
    private String dataType;
    @JsonProperty("isSink")
    private boolean sink = false;
}
