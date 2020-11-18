package org.hetida.designer.backend.converter;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.OutputWiringDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.InputWiringDTO;
import org.hetida.designer.backend.dto.engine.WorkflowWiringDTO;
import org.hetida.designer.backend.exception.InputWiringException;
import org.hetida.designer.backend.model.Filter;
import org.hetida.designer.backend.model.InputWiring;
import org.hetida.designer.backend.model.OutputWiring;
import org.hetida.designer.backend.model.Wiring;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@Component
@Log4j2
public class WorkflowWiringConverter {

    private final ObjectMapper objectMapper = new ObjectMapper();

    public Wiring toWiring(org.hetida.designer.backend.dto.WiringDTO wiringDTO) {

        Wiring wiring = new Wiring();

        UUID wiringId = wiringDTO.getId();

        wiring.setId(wiringId);
        wiring.setName(wiringDTO.getName());

        List<OutputWiring> outputWirings = wiringDTO.getOutputWirings().stream().map(inputDto -> {
            OutputWiring tmpOutputWiring = new OutputWiring();
            tmpOutputWiring.setId(inputDto.getId());
            tmpOutputWiring.setAdapterId(inputDto.getAdapterId().toString());
            tmpOutputWiring.setWiringId(wiringId);
            tmpOutputWiring.setSinkId(inputDto.getSinkId());
            tmpOutputWiring.setWorkflowOutputName(inputDto.getWorkflowOutputName());
            return tmpOutputWiring;
        }).collect(Collectors.toList());

        wiring.setOutputWirings(outputWirings);


        List<InputWiring> inputWirings = wiringDTO.getInputWirings().stream().map(inputWiring -> {
            List<Filter> filters = new ArrayList<>();


            if(inputWiring.getFilters() != null) {
                inputWiring.getFilters().forEach((key, value) -> {
                    if(key == null || value == null) {
                        return;
                    }
                    Filter filter = new Filter();
                    filter.setInputWiringId(inputWiring.getId());
                    filter.setKey(key);
                    filter.setValue(value);
                    filters.add(filter);
                });
            }


            InputWiring tmpInputWiring = new InputWiring();
            tmpInputWiring.setId(inputWiring.getId());
            tmpInputWiring.setAdapterId(inputWiring.getAdapterId().toString());
            tmpInputWiring.setWiringId(wiringId);
            tmpInputWiring.setInputFilters(filters);
            tmpInputWiring.setSourceId(inputWiring.getSourceId());
            tmpInputWiring.setWorkflowInputName(inputWiring.getWorkflowInputName());
            return tmpInputWiring;
        }).collect(Collectors.toList());

        wiring.setInputWirings(inputWirings);


        return wiring;
    }

    public List<WiringDTO> toWiringDtos(List<Wiring> wirings) {
        return wirings.stream().map(this::toWiringDto).collect(Collectors.toList());
    }

    public org.hetida.designer.backend.dto.WiringDTO toWiringDto(Wiring wiring){
        org.hetida.designer.backend.dto.WiringDTO wiringDTO = new org.hetida.designer.backend.dto.WiringDTO();

        wiringDTO.setId(wiring.getId());
        wiringDTO.setName(wiring.getName());

        List<org.hetida.designer.backend.dto.InputWiringDTO> inputWirings = wiring.getInputWirings().stream().map(inputWiring -> {
            org.hetida.designer.backend.dto.InputWiringDTO tmpInputWiring = new org.hetida.designer.backend.dto.InputWiringDTO();
            tmpInputWiring.setId(inputWiring.getId());
            tmpInputWiring.setAdapterId(Integer.parseInt(inputWiring.getAdapterId()));

            Map<String, String> filterMap = new HashMap<>();
            inputWiring.getInputFilters().forEach(f -> filterMap.put(f.getKey(), f.getValue()));

            tmpInputWiring.setFilters(filterMap);
            tmpInputWiring.setSourceId(inputWiring.getSourceId());
            tmpInputWiring.setWorkflowInputName(inputWiring.getWorkflowInputName());
            return tmpInputWiring;
        }).collect(Collectors.toList());

        wiringDTO.setInputWirings(inputWirings);

        List<OutputWiringDTO> outputWirings = wiring.getOutputWirings().stream().map(outputWiring -> {
            OutputWiringDTO tmpOutputWiring = new OutputWiringDTO();
            tmpOutputWiring.setId(outputWiring.getId());
            tmpOutputWiring.setAdapterId(Integer.parseInt(outputWiring.getAdapterId()));
            tmpOutputWiring.setSinkId(outputWiring.getSinkId());
            tmpOutputWiring.setWorkflowOutputName(outputWiring.getWorkflowOutputName());
            return tmpOutputWiring;
        }).collect(Collectors.toList());

        wiringDTO.setOutputWirings(outputWirings);

        return wiringDTO;
    }
    public WorkflowWiringDTO convertWorkflowWiringDTO(org.hetida.designer.backend.dto.WiringDTO wiringToConvert){
        if (wiringToConvert == null)
            return null;
        WorkflowWiringDTO result = new WorkflowWiringDTO();
        result.setInputWirings(convertInputWirings(wiringToConvert.getInputWirings()));
        result.setOutputWirings(convertOutputWirings(wiringToConvert.getOutputWirings()));
        return result;
    }

    private List<InputWiringDTO> convertInputWirings(List<org.hetida.designer.backend.dto.InputWiringDTO> inputWiringsToConvert){
        return inputWiringsToConvert.stream().map(this::convertInputWiringDTO).collect(Collectors.toList());
    }

    private List<org.hetida.designer.backend.dto.engine.OutputWiringDTO> convertOutputWirings(List<org.hetida.designer.backend.dto.OutputWiringDTO> outputWiringsToConvert){
        return outputWiringsToConvert.stream().map(this::convertOutputWiringDTO).collect(Collectors.toList());
    }

    private org.hetida.designer.backend.dto.engine.OutputWiringDTO convertOutputWiringDTO (org.hetida.designer.backend.dto.OutputWiringDTO outputWiringToConvert){
        org.hetida.designer.backend.dto.engine.OutputWiringDTO result = new org.hetida.designer.backend.dto.engine.OutputWiringDTO();
        result.setAdapterId(outputWiringToConvert.getAdapterId());
        result.setSinkId(outputWiringToConvert.getSinkId());
        result.setWorkflowOutputName(outputWiringToConvert.getWorkflowOutputName());
        return result;
    }

    private InputWiringDTO convertInputWiringDTO (org.hetida.designer.backend.dto.InputWiringDTO inputWiringToConvert){
        InputWiringDTO result = new InputWiringDTO();
        result.setAdapterId(inputWiringToConvert.getAdapterId());
        result.setSourceId(inputWiringToConvert.getSourceId());
        result.setWorkflowInputName(inputWiringToConvert.getWorkflowInputName());
        if (inputWiringToConvert.getFilters() != null ){
            for ( String key : inputWiringToConvert.getFilters().keySet() ){
                try {
                    if(inputWiringToConvert.getFilters().get(key) == null){
                        continue;
                    }
                    result.getFilters().put(key, objectMapper.readValue(inputWiringToConvert.getFilters().get(key), HashMap.class));
                } catch (IOException e) {
                    try {
                        result.getFilters().put(key, inputWiringToConvert.getFilters().get(key) );
                    } catch (Exception e1) {
                        log.error(e1);
                        throw new InputWiringException("error while deserializing filters", e1);
                    }
                }
            }
        }
        return result;
    }


}
