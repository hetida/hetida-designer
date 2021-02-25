package org.hetida.designer.demo.adapter.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.Data;

@Data
public class SinkDTO {
    private String id;
    private String thingNodeId;
    private String name;
    @JsonInclude(JsonInclude.Include.NON_NULL)
    private String metadataKey;
    private String type;
    private boolean visible = true;
    private String path;
}
