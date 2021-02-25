package org.hetida.designer.demo.adapter.dto.client;

import lombok.Data;
import org.hetida.designer.demo.adapter.dto.MetaDataDTO;

import java.util.List;

@Data
public class ClientMetaDataDTO {
    List<MetaDataDTO> metadata;
}
