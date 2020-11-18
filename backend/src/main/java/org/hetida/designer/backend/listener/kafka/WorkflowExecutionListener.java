package org.hetida.designer.backend.listener.kafka;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.listener.kafka.converter.ExecutionConverter;
import org.hetida.designer.backend.listener.kafka.converter.ExecutionResultConverter;
import org.hetida.designer.backend.listener.kafka.dto.ExecutionResultDTO;
import org.hetida.designer.backend.listener.kafka.dto.WiredExecutionDTO;
import org.hetida.designer.backend.service.KafkaService;
import org.hetida.designer.backend.service.WorkflowExecutionService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;
import java.io.IOException;

@Component
@Log4j2
public class WorkflowExecutionListener {

    private final ExecutionConverter executionConverter;
    private final WorkflowExecutionService workflowExecutionService;
    private final KafkaService kafkaService;
    private final ExecutionResultConverter executionResultConverter;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${org.hetida.designer.backend.listener.kafka.execResultTopic:h4w_designer_job_result}")
    private String resultTopic;

    public WorkflowExecutionListener(ExecutionConverter executionConverter, WorkflowExecutionService workflowExecutionService,
                                     ExecutionResultConverter executionResultConverter, KafkaService kafkaService){
        this.executionConverter = executionConverter;
        this.workflowExecutionService = workflowExecutionService;
        this.executionResultConverter = executionResultConverter;
        this.kafkaService = kafkaService;
    }

    @KafkaListener(topics = "${org.hetida.designer.backend.listener.kafka.execTopic:h4w_designer_initialize_job}",
                   autoStartup = "${org.hetida.designer.backend.listener.kafka.enabled}")
    public void processExecution(@Payload String content,
                                 @Header(KafkaHeaders.RECEIVED_MESSAGE_KEY) String key){
        WiredExecutionDTO kfkExecDto = null;
        ExecutionResultDTO executionResultDTO = null;
        try {
            kfkExecDto = objectMapper.readValue(content, WiredExecutionDTO.class);
        } catch (IOException ex) {
            log.error(ex);
            executionResultDTO = executionResultConverter.convertFromException(ex);
        }
        if (kfkExecDto != null){
            try{
                WiringDTO wiringDTO = executionConverter.convertWorkflowWiringDtoToWiringDTO(kfkExecDto.getWorkflow_wiring());
                ExecutionResponseDTO executionResponseDTO = this.workflowExecutionService.execute(
                        wiringDTO, executionConverter.convertConfigurationDTO(kfkExecDto.getConfiguration()), kfkExecDto.getWorkflowId());
                executionResultDTO = executionResultConverter.convertToExecutionResultDTO(executionResponseDTO);

            }
            catch(Exception ex){
                log.error(ex);
                executionResultDTO = executionResultConverter.convertFromException(ex);
            }
        }
        try {
            String resultJson = objectMapper.writeValueAsString(executionResultDTO);
            kafkaService.sendMessage( resultTopic, key, resultJson);
        }
        catch(Exception ex){
            log.error(ex);
        }
    }

}
