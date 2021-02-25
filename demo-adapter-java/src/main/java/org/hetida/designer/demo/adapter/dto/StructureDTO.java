package org.hetida.designer.demo.adapter.dto;


import lombok.Data;

import java.util.List;

@Data
public class StructureDTO {
    private String id;
    private String name;
    private List<ThingNodeDTO> thingNodes;
    private List<SourceDTO> sources;
    private List<SinkDTO> sinks;
}
