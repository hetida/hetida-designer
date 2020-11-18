package org.hetida.designer.backend.listener.kafka.converter;

import org.hetida.designer.backend.dto.ConfigurationDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.listener.kafka.dto.WorkflowWiringDTO;
import org.springframework.stereotype.Component;

@Component
public class ExecutionConverter {

    private final WiringConverter workflowWiringConverter;

    public ExecutionConverter(WiringConverter workflowWiringConverter){
        this.workflowWiringConverter = workflowWiringConverter;
    }


    public WiringDTO convertWorkflowWiringDtoToWiringDTO(WorkflowWiringDTO workflowWiringDTO){
        return workflowWiringConverter.convertWorkflowWiringDTO(workflowWiringDTO);
    }

    public ConfigurationDTO convertConfigurationDTO(org.hetida.designer.backend.listener.kafka.dto.ConfigurationDTO configurationDTO){
        ConfigurationDTO result = new ConfigurationDTO();
        result.setEngine(configurationDTO.getEngine());
        result.setName(configurationDTO.getName());
        result.setRun_pure_plot_operators(configurationDTO.isRun_pure_plot_operators());
        return result;
    }


}
