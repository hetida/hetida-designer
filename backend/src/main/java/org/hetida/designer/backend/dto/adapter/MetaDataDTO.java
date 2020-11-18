package org.hetida.designer.backend.dto.adapter;


import lombok.Data;

import java.util.List;

@Data
public class MetaDataDTO {
    private Integer id;
    private String name;
    private List<ThingNodeDTO> thingNodes;
    private List<SourceDTO> sources;
    private List<SinkDTO> sinks;
}
