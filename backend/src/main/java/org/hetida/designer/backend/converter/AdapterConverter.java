package org.hetida.designer.backend.converter;

import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.springframework.stereotype.Component;

@Component
public class AdapterConverter {

    public ModulAdapterDTO convertMapToDTOs(String adapterId, String name, String adapterUrl, String internalAdapterUrl) {
        ModulAdapterDTO adapterDTO = new ModulAdapterDTO();
        adapterDTO.setId(adapterId);
        adapterDTO.setName(name);
        adapterDTO.setUrl(adapterUrl);
        adapterDTO.setInternalUrl(internalAdapterUrl);
        return adapterDTO;
    }
}
