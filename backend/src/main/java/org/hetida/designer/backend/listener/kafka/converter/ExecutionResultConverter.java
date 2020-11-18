package org.hetida.designer.backend.listener.kafka.converter;

import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.listener.kafka.dto.ExecutionErrorDTO;
import org.hetida.designer.backend.listener.kafka.dto.ExecutionResultDTO;
import org.springframework.stereotype.Component;

@Component
public class ExecutionResultConverter {

    private static final String EXEC_ERROR_CODE = "WORKFLOW_EXECUTION_ERROR";

    public ExecutionResultDTO convertToExecutionResultDTO(ExecutionResponseDTO responseDTO){
        ExecutionResultDTO result = new ExecutionResultDTO();
        if (responseDTO.getError() != null ){
            ExecutionErrorDTO errorDTO = new ExecutionErrorDTO();
            result.getErrors().add(errorDTO);
            errorDTO.setCode(EXEC_ERROR_CODE);
            errorDTO.setMessage(responseDTO.getError());
            result.setSuccess(false);

        }
        else{
            result.setSuccess(true);
            result.setOutput_results_by_output_name(responseDTO.getOutput_results_by_output_name());
            result.setOutput_types_by_output_name(responseDTO.getOutput_types_by_output_name());
        }
        return result;
    }

    public ExecutionResultDTO convertFromException(Exception ex){
        ExecutionResultDTO executionResultDTO = new ExecutionResultDTO();
        executionResultDTO.setSuccess(false);
        ExecutionErrorDTO error = new ExecutionErrorDTO();
        error.setCode(EXEC_ERROR_CODE);
        error.setMessage(ex.getMessage());
        executionResultDTO.getErrors().add(new ExecutionErrorDTO());
        return executionResultDTO;
    }

}
