package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.adapter.MetaDataDTO;
import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.hetida.designer.backend.enums.Adapter;

import java.util.List;

public interface AdapterService {

    @Deprecated
    List<Adapter> getAllAdapters();

    @Deprecated
    MetaDataDTO getMetaData(Adapter adapter);

    List<ModulAdapterDTO> getAllInstalledAdapters();
}
