package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.model.Component;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public interface ComponentService {
    Map<UUID, Component> findAllById(List<UUID> uuids);

    Component findById(UUID id);

    Component create(Component component);

    Component update(Component component);

	  Component bindWiring(UUID id, WiringDTO wiringDto);
    
    void delete(UUID id);
}
