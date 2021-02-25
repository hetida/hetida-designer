package org.hetida.designer.demo.adapter.dto.client;

import lombok.Data;

@Data
public class ClientStructureDTO {

    private ClientThingNodesDTO thingNodes;
    private ClientSourcesDTO sources;
    private ClientSinksDTO sinks;
}
