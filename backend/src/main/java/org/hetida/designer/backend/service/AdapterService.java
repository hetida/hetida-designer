package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;


import java.util.List;

public interface AdapterService {
    List<ModulAdapterDTO> getAllInstalledAdapters();
}
