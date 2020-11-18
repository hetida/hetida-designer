package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.adapter.AdapterProvider;
import org.hetida.designer.backend.converter.AdapterConverter;
import org.hetida.designer.backend.dto.adapter.MetaDataDTO;
import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.hetida.designer.backend.enums.Adapter;
import org.hetida.designer.backend.service.AdapterService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Log4j2
public class AdapterServiceImpl implements AdapterService {

    private final AdapterProvider adapterProvider;
    private final AdapterConverter adapterConverter;

    @Value("${org.hetida.designer.backend.installed.adapters}")
    private String adapters;


    public AdapterServiceImpl(AdapterProvider adapterProvider, AdapterConverter adapterConverter){
        this.adapterProvider = adapterProvider;
        this.adapterConverter = adapterConverter;
    }

    @Deprecated
    @Override
    public List<Adapter> getAllAdapters() {
        List<Adapter> resultList = new ArrayList<>();
        for (Adapter adapter : Adapter.values()){
            switch (adapter){
                case MANUAL: resultList.add(adapter); break;
                default: resultList.add(adapter);
            }
        }
        return resultList;
    }

    @Deprecated
    public MetaDataDTO getMetaData(Adapter adapter) {
        org.hetida.designer.backend.adapter.AdapterService adapterService = adapterProvider.getAdapterService(adapter);
        return adapterService != null ? adapterService.getMetaData() : null;
    }

    @Override
    public List<ModulAdapterDTO> getAllInstalledAdapters() {

        List<ModulAdapterDTO> resultList = new ArrayList<>();
        Map<String, String> adaptersMap = Arrays.stream(adapters.split(","))
                .map(s -> s.split(":", 2))
                .collect(Collectors.toMap(s -> s[0].trim(), s -> s[1].trim()));
        adaptersMap.forEach((id, url) -> resultList.add(adapterConverter.convertMapToDTOs(id, url)));

        return resultList;
    }
}
