package org.hetida.designer.demo.adapter.dto.client;

import lombok.Data;
import org.hetida.designer.demo.adapter.dto.SourceDTO;

import java.util.List;

@Data
public class ClientSourcesDTO {
    List<ClientSourceDTO> sources;
}
