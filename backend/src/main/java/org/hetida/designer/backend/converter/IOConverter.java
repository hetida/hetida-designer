package org.hetida.designer.backend.converter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.IODTO;
import org.hetida.designer.backend.dto.WorkflowIODTO;
import org.hetida.designer.backend.model.BaseIO;
import org.hetida.designer.backend.model.ComponentIO;
import org.hetida.designer.backend.model.WorkflowIO;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
@Log4j2
public class IOConverter {
    private final ObjectMapper objectMapper = new ObjectMapper();

    private static final String VALUE_KEY="value";

    public List<WorkflowIO> convertWorkflowIODTOToEntities(final List<WorkflowIODTO> dtos) {
        return dtos == null ? null : dtos.stream()
                .map(this::convertWorkflowIODTOToEntity)
                .collect(Collectors.toList());
    }

    public List<WorkflowIODTO> convertWorkflowIOToWorkflowIODTOs(final List<WorkflowIO> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertWorkflowIOToWorkflowIODTO)
                .collect(Collectors.toList());
    }

    public List<IODTO> convertWorkflowIOToOperatorIODtos(final List<WorkflowIO> entities) {
        return entities == null ? null : entities.stream().filter(x -> !x.isConstant())
                .map(this::convertBaseIOToIODto)
                .collect(Collectors.toList());
    }

    public List<IODTO> convertWorkflowIOToIODtos(final List<WorkflowIO> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertBaseIOToIODto)
                .collect(Collectors.toList());
    }

    public List<IODTO> convertComponentIOToIODtos(final List<ComponentIO> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertBaseIOToIODto)
                .collect(Collectors.toList());
    }

    public List<ComponentIO> convertToComponentIOEntities(final List<IODTO> dtos) {
        return dtos == null ? null : dtos.stream()
                .map(this::convertToComponentIOEntity)
                .collect(Collectors.toList());
    }

    private WorkflowIO convertWorkflowIODTOToEntity(WorkflowIODTO dto) {
        WorkflowIO io = new WorkflowIO();
        io.setType(dto.getType());
        io.setId(dto.getId());
        io.setPosX(dto.getPosX());
        io.setPosY(dto.getPosY());
        io.setOperator(dto.getOperator());
        io.setConnector(dto.getConnector());
        io.setConstant(dto.isConstant());
        io.setConstantValue(dto.getConstantValue());
        io.setName(dto.isConstant() ? null : dto.getName());
        if(io.getConstantValue()!=null){
            Object value=io.getConstantValue().get(VALUE_KEY);
            if(value != null && !StringUtils.isEmpty(value.toString())){
                String valueAsString = value.toString();
                switch (io.getType()){
                  case BOOLEAN:{
                    io.getConstantValue().put(VALUE_KEY, Boolean.parseBoolean(valueAsString));
                    break;
                  }
                  case FLOAT:{
                    io.getConstantValue().put(VALUE_KEY, Float.parseFloat(valueAsString));
                    break;
                  }
                  case INT:{
                    io.getConstantValue().put(VALUE_KEY, Integer.parseInt(valueAsString));
                    break;
                  }
                  case STRING:{
                    io.getConstantValue().put(VALUE_KEY, valueAsString);
                    break;
                  }
                  default:{
                    Map<String, Object> jsonMap = new HashMap<>();
                    try {
                      TypeReference<HashMap<String,Object>> typeRef = new TypeReference<HashMap<String,Object>>() {};
                      jsonMap=objectMapper.readValue(valueAsString, typeRef);
                    } catch (IOException e) {
                      log.info("could not parse constant value " +  valueAsString);
                    }
                    io.getConstantValue().put(VALUE_KEY, jsonMap);
                  }
                }
            }
        }

        return io;
    }

    private WorkflowIODTO convertWorkflowIOToWorkflowIODTO(WorkflowIO entity) {
        WorkflowIODTO ioDTO = new WorkflowIODTO();
        ioDTO.setType(entity.getType());
        ioDTO.setName(entity.getName());
        ioDTO.setId(entity.getId());
        ioDTO.setPosX(entity.getPosX());
        ioDTO.setPosY(entity.getPosY());
        ioDTO.setOperator(entity.getOperator());
        ioDTO.setConnector(entity.getConnector());
        ioDTO.setConstant(entity.isConstant());
        ioDTO.setConstantValue(entity.getConstantValue());
        if(ioDTO.getConstantValue()!=null){
            Object value=ioDTO.getConstantValue().get(VALUE_KEY);
            if(value != null){
                String valueAsString=value.toString();
                if(!StringUtils.isEmpty(valueAsString)){
                    switch (ioDTO.getType()){
                        case BOOLEAN:{
                            ioDTO.getConstantValue().put(VALUE_KEY, valueAsString);
                            break;
                        }
                        case FLOAT:{
                            ioDTO.getConstantValue().put(VALUE_KEY, valueAsString);
                            break;
                        }
                        case INT:{
                            ioDTO.getConstantValue().put(VALUE_KEY, valueAsString);
                            break;
                        }
                        case STRING:{
                            ioDTO.getConstantValue().put(VALUE_KEY, valueAsString);
                            break;
                        }
                        default:{
                            String jsonString="";
                            try {
                                jsonString=objectMapper.writeValueAsString(value);
                            } catch (JsonProcessingException e) {
                                log.info("could not map json object " + valueAsString);
                            }
                            ioDTO.getConstantValue().put(VALUE_KEY, jsonString);
                        }
                    }

                }
            }
        }
        return ioDTO;
    }

    private IODTO convertBaseIOToIODto(BaseIO entity) {
        IODTO ioDTO = new IODTO();
        ioDTO.setType(entity.getType());
        ioDTO.setName(entity.getName());
        ioDTO.setId(entity.getId());
        ioDTO.setPosX(entity.getPosX());
        ioDTO.setPosY(entity.getPosY());
        return ioDTO;
    }

    private ComponentIO convertToComponentIOEntity(IODTO dto) {
        ComponentIO io = new ComponentIO();
        io.setType(dto.getType());
        io.setName(dto.getName());
        io.setId(dto.getId());
        return io;
    }

}
