package org.hetida.designer.backend.service;


import org.hetida.designer.backend.model.Documentation;

import java.util.UUID;

public interface DocumentationService {
    Documentation findById(UUID id);

    void update(Documentation component);

    void delete(UUID id);
}
