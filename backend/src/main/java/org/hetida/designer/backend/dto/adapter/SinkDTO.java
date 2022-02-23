package org.hetida.designer.backend.dto.adapter;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class SinkDTO {
    private String id;
    private String name;
    private String thingNodeId;
    private String dataType;
}
