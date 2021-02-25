package org.hetida.designer.demo.adapter.converter;

import lombok.NonNull;
import org.hetida.designer.demo.adapter.dto.SinkDTO;
import org.hetida.designer.demo.adapter.dto.client.ClientSinkDTO;
import org.hetida.designer.demo.adapter.dto.client.ClientSinksDTO;
import org.hetida.designer.demo.adapter.dto.client.ClientStructureDTO;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class SinkDataConverter {

    public List<SinkDTO> convertClientStructureToSinks(ClientStructureDTO clientStructureDTO) {
        return convertClientSinksToSinks(clientStructureDTO.getSinks());
    }

    public List<SinkDTO> convertClientSinksToSinks(ClientSinksDTO sinks) {
        List<SinkDTO> sinkDTOS = new ArrayList<>();
        sinks.getSinks().forEach(s -> {
            SinkDTO sinkDTO = new SinkDTO();
            sinkDTO.setId(s.getId());
            sinkDTO.setName(s.getName());
            sinkDTO.setType(s.getType().getName());
            sinkDTO.setMetadataKey(determineMetadataKey(s));
            sinkDTO.setThingNodeId(s.getThingNodeId());
            sinkDTO.setPath(s.getPath());
            sinkDTO.setVisible(s.isVisible());
            sinkDTOS.add(sinkDTO);
        });
        return sinkDTOS;
    }

    private String determineMetadataKey(@NonNull ClientSinkDTO dto) {
        if (dto.getType().getName().startsWith("metadata")) {
            return dto.getName();
        }
        return null;
    }
}
