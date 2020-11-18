package org.hetida.designer.backend.dto.adapter;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class SourceDTO {
    private String id;
    private String name;
    private String thingNodeId;
    private String dataType;
    private Map<String, FilterDTO> filters;
}
