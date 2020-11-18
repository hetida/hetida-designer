package org.hetida.designer.backend.listener.kafka.converter;

import org.hetida.designer.backend.dto.InputWiringDTO;
import org.hetida.designer.backend.dto.OutputWiringDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class WiringConverter {

    public WiringDTO convertWorkflowWiringDTO(org.hetida.designer.backend.listener.kafka.dto.WorkflowWiringDTO workflowWiring){
        WiringDTO result = new WiringDTO();
        result.setInputWirings(convertInputWirings(workflowWiring.getInput_wirings()));
        result.setOutputWirings(convertOutputWirings(workflowWiring.getOutput_wirings()));
        return result;
    }

    private List<InputWiringDTO> convertInputWirings(List<org.hetida.designer.backend.listener.kafka.dto.InputWiringDTO> inputWirings){
        return inputWirings.stream().map(this::convertInputWiring).collect(Collectors.toList());
    }

    private InputWiringDTO convertInputWiring(org.hetida.designer.backend.listener.kafka.dto.InputWiringDTO inputWiring){
        InputWiringDTO result = new InputWiringDTO();
        result.setAdapterId(inputWiring.getAdapter_id());
        result.setSourceId(inputWiring.getSource_id());
        result.setWorkflowInputName(inputWiring.getWorkflow_input_name());
        result.setFilters(inputWiring.getFilters());
        return result;
    }

    private List<OutputWiringDTO> convertOutputWirings(List<org.hetida.designer.backend.listener.kafka.dto.OutputWiringDTO> outputWirings){
        return outputWirings.stream().map(this::convertOutputWiring).collect(Collectors.toList());
    }

    private OutputWiringDTO convertOutputWiring(org.hetida.designer.backend.listener.kafka.dto.OutputWiringDTO outputWiring){
        OutputWiringDTO result = new OutputWiringDTO();
        result.setAdapterId(outputWiring.getAdapter_id());
        result.setSinkId(outputWiring.getSink_id());
        result.setWorkflowOutputName(outputWiring.getWorkflow_output_name());
        return result;
    }




}
