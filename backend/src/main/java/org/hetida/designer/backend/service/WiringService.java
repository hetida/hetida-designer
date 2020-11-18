package org.hetida.designer.backend.service;

import java.util.List;

import org.hetida.designer.backend.model.Wiring;

public interface WiringService {
    Wiring create(Wiring wiring);
    Wiring update(Wiring wiring);
    List<Wiring> getAll();
}