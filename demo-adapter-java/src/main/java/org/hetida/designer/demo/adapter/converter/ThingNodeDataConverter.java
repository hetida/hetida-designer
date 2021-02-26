package org.hetida.designer.demo.adapter.converter;

import org.hetida.designer.demo.adapter.dto.StructureDTO;
import org.hetida.designer.demo.adapter.dto.ThingNodeDTO;
import org.hetida.designer.demo.adapter.dto.client.ClientStructureDTO;
import org.hetida.designer.demo.adapter.dto.client.ClientThingNodesDTO;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class ThingNodeDataConverter {

    private final SourceDataConverter sourceDataConverter;
    private final SinkDataConverter sinkDataConverter;
    @Value("${demo.adapter.id}")
    private String adapterId;
    @Value("${demo.adapter.name}")
    private String adapterName;

    public ThingNodeDataConverter(SourceDataConverter sourceDataConverter, SinkDataConverter sinkDataConverter) {
        this.sourceDataConverter = sourceDataConverter;
        this.sinkDataConverter = sinkDataConverter;
    }

    public StructureDTO convertToStructureDto(ClientStructureDTO clientStructureDTO) {
        StructureDTO structureDTO = new StructureDTO();
        structureDTO.setId(adapterId);
        structureDTO.setName(adapterName);
        structureDTO.setThingNodes(convertClientStructureToThingNodes(clientStructureDTO.getThingNodes()));
        structureDTO.setSources(sourceDataConverter.convertClientStructureToSources(clientStructureDTO));
        structureDTO.setSinks(sinkDataConverter.convertClientStructureToSinks(clientStructureDTO));
        return structureDTO;
    }

    private List<ThingNodeDTO> convertClientStructureToThingNodes(ClientThingNodesDTO thingNodes) {
        List<ThingNodeDTO> thingNodeDTOS = new ArrayList<>();
        thingNodes.getThingNodes().forEach(n -> {
            ThingNodeDTO thingNodeDTO = new ThingNodeDTO();
            thingNodeDTO.setId(n.getId());
            thingNodeDTO.setParentId(n.getParentId());
            thingNodeDTO.setName(n.getName());
            thingNodeDTO.setDescription(n.getDescription());
            thingNodeDTOS.add(thingNodeDTO);
        });
        return thingNodeDTOS;
    }
}
