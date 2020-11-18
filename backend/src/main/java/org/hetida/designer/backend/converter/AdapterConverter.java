package org.hetida.designer.backend.converter;

import org.hetida.designer.backend.dto.adapter.AdapterDTO;
import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.hetida.designer.backend.enums.Adapter;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class AdapterConverter {

    public List<AdapterDTO> convertToDTOs(List<Adapter> adapters){
        return adapters.stream().map(this::convertAdapterToDto).collect(Collectors.toList());
    }

    public ModulAdapterDTO convertMapToDTOs(String adapterId, String adapterUrl) {
        ModulAdapterDTO adapterDTO = new ModulAdapterDTO();
        adapterDTO.setId(adapterId);
        adapterDTO.setName("");
        adapterDTO.setUrl(adapterUrl);

        return adapterDTO;
    }

    private AdapterDTO convertAdapterToDto(Adapter adapter){
        AdapterDTO adapterDTO = new AdapterDTO();
        adapterDTO.setId(adapter.getId());
        adapterDTO.setName(adapter.getName());
        return adapterDTO;
    }

}
