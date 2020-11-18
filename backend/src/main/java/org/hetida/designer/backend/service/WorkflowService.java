package org.hetida.designer.backend.service;

import org.hetida.designer.backend.dto.WorkflowDTO;
import org.hetida.designer.backend.dto.WorkflowSummaryDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.model.Workflow;
import org.hetida.designer.backend.model.WorkflowOperator;

import java.util.List;
import java.util.Map;
import java.util.UUID;

public interface WorkflowService {

    List<WorkflowSummaryDTO> summarizeAll();

    Workflow findById(UUID id);

    WorkflowDTO dtoById(UUID id);

    Workflow create(Workflow workflow);

    Workflow update(Workflow workflow);

    void delete(UUID id);

    List<WorkflowOperator> getWorkflowOperatorsRecursive(Workflow workflow);

    Map<UUID, Component> getAllComponents(List<WorkflowOperator> workflowOperators);

    Map<UUID, Workflow> getAllWorkflows(List<WorkflowOperator> workflowOperators);

	void bindWiring(UUID id, WiringDTO wiringDto);
}
