package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.AdapterConverter;
import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.hetida.designer.backend.service.AdapterService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

import java.util.ArrayList;
import java.util.List;

@Service
@Log4j2
public class AdapterServiceImpl implements AdapterService {

    private final AdapterConverter adapterConverter;

    @Value("${org.hetida.designer.backend.installed.adapters}")
    private String adapters;


    public AdapterServiceImpl(AdapterConverter adapterConverter){
        this.adapterConverter = adapterConverter;
    }

    @Override
    public List<ModulAdapterDTO> getAllInstalledAdapters() {
        List<ModulAdapterDTO> resultList = new ArrayList<>();
        if (adapters == null || adapters.trim().length() == 0)
          return resultList;

        for (String adapterStr : adapters.split(",")) {
          String[] adapterPropsStr = adapterStr.split("\\|");
          Assert.isTrue(adapterPropsStr.length == 4,
            "Wrong adapter configuration format - must be \"id|name|url,id2|name2|url2,...\"");
          resultList.add(adapterConverter.convertMapToDTOs(adapterPropsStr[0], adapterPropsStr[1], adapterPropsStr[2], adapterPropsStr[3]));
        }
        return resultList;
    }
}
