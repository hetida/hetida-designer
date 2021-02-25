package org.hetida.designer.demo.adapter.converter;

import org.hetida.designer.demo.adapter.dto.MetaDataDTO;
import org.hetida.designer.demo.adapter.dto.MetaDataRequestResponseDTO;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

import static org.hetida.designer.demo.adapter.util.AdapterUtil.getKeyFromString;

@Component
public class MetaDataConverter {

    public List<MetaDataRequestResponseDTO> convertToMetaDataRequestResponseDTOs(List<MetaDataDTO> metaDataDTOS) {
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTOS = new ArrayList<>();
        metaDataDTOS.forEach(dto -> metaDataRequestResponseDTOS.add(convertToMetaDataRequestResponseDTO(dto)));
        return metaDataRequestResponseDTOS;
    }

    private MetaDataRequestResponseDTO convertToMetaDataRequestResponseDTO(MetaDataDTO dto) {
        MetaDataRequestResponseDTO metaDataRequestResponseDTO = new MetaDataRequestResponseDTO();
        metaDataRequestResponseDTO.setKey(getKeyFromString(dto.getKey()));
        metaDataRequestResponseDTO.setValue(dto.getValue().toString());
        metaDataRequestResponseDTO.setDataType(dto.getDataType().getName());
        metaDataRequestResponseDTO.setSink(dto.isSink());
        return metaDataRequestResponseDTO;
    }

}
