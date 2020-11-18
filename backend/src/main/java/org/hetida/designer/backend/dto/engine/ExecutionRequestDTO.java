package org.hetida.designer.backend.dto.engine;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class ExecutionRequestDTO {
    private WorkflowNodeDTO workflow;
    private List<CodeModuleDTO> code_modules = new ArrayList<>();
    private List<ComponentDTO> components = new ArrayList<>();
    private ConfigurationDTO configuration;
    private WorkflowWiringDTO workflow_wiring;


}
