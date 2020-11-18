package org.hetida.designer.backend.listener.kafka.dto;

import lombok.Data;
import org.hetida.designer.backend.enums.IOType;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Data
public class ExecutionResultDTO {
    private Boolean success;
    private List<ExecutionErrorDTO> errors = new ArrayList<>();
    private Map<String, Object> output_results_by_output_name;
    private Map<String, IOType> output_types_by_output_name;

}
