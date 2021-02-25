package org.hetida.designer.demo.adapter.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

import java.util.Map;

@Data
public class SourceDTO {
    private String id;
    private String thingNodeId;
    private String name;
    private String type;
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private String metadataKey;
    private boolean visible = true;
    private String path;
    private Map<String, FilterDTO> filters;
}
