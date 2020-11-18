package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.apache.commons.collections4.IterableUtils;
import org.hetida.designer.backend.converter.BaseItemConverter;
import org.hetida.designer.backend.dto.BaseItemDTO;
import org.hetida.designer.backend.repository.ComponentRepository;
import org.hetida.designer.backend.repository.WorkflowRepository;
import org.hetida.designer.backend.service.BaseItemService;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@Log4j2
public class BaseItemServiceImpl implements BaseItemService {
    private final ComponentRepository componentRepository;
    private final WorkflowRepository workflowRepository;
    private final BaseItemConverter baseItemConverter;

    public BaseItemServiceImpl(ComponentRepository componentRepository, WorkflowRepository workflowRepository, BaseItemConverter baseItemConverter) {
        this.componentRepository = componentRepository;
        this.workflowRepository = workflowRepository;
        this.baseItemConverter = baseItemConverter;
    }

    @Override
    public List<BaseItemDTO> getAllBaseItems() {
        final List<BaseItemDTO> baseItemList = new ArrayList<>();
        baseItemList.addAll(this.baseItemConverter.convertComponentsToDtos(IterableUtils.toList(this.componentRepository.findAll())));
        baseItemList.addAll(this.baseItemConverter.convertWorkflowsToDtos(IterableUtils.toList(this.workflowRepository.findAll())));
        return baseItemList;
    }


}
