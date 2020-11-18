package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.client.KeycloakClient;
import org.hetida.designer.backend.dto.engine.CodegenRequestDTO;
import org.hetida.designer.backend.dto.engine.CodegenResponseDTO;
import org.hetida.designer.backend.dto.engine.ExecutionRequestDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.enums.IOType;
import org.hetida.designer.backend.exception.RuntimeEngineException;
import org.hetida.designer.backend.service.EngineService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
@Log4j2
public class EngineServiceImpl implements EngineService {

    private static final String ENGINE_IS_DISABLED = "engine is disabled";

    @Value("${org.hetida.designer.backend.runtime}")
    private String engineUri;

    @Value("${org.hetida.designer.backend.codegen}")
    private String codegenUri;

    @Value("${org.hetida.designer.backend.engineEnabled}")
    private boolean engineEnabled;

    @Value("${keycloak.enabled:false}")
    private boolean keycloakEnabled;

    @Value("${org.hetida.designer.backend.engine.keycloak.client:hetida-designer-runtime}")
    private String engineClient;

    @Value("${org.hetida.designer.backend.engine.keycloak.user:serviceuser}")
    private String engineUser;

    @Value("${org.hetida.designer.backend.engine.keycloak.password:password}")
    private String enginePassword;

    @Value("${keycloak.auth-server-url:localhost}")
    private String keycloakUrl;

    @Value("${keycloak.realm:Hetida}")
    private String keycloakRealm;

    private final KeycloakClient keycloakClient;

    public EngineServiceImpl(KeycloakClient keycloakClient){
        this. keycloakClient = keycloakClient;
    }


    @Override
    public ExecutionResponseDTO executeWorkflow(ExecutionRequestDTO workflowExecutionRequest) throws RuntimeEngineException{
        try {

            RestTemplate restTemplate = new RestTemplate();
            log.debug("process workflow execution");
            log.debug("engine request ({}):", engineUri);
            log.debug(workflowExecutionRequest.toString());
            //temporary post to mock engine
            ExecutionResponseDTO executionResponse;
            if(this.engineEnabled){
                HttpHeaders headers = new HttpHeaders();
                if (keycloakEnabled){
                    headers.add(HttpHeaders.AUTHORIZATION, keycloakClient.getToken(keycloakUrl, keycloakRealm, engineClient, engineUser, enginePassword));
                }
                HttpEntity<ExecutionRequestDTO> entity = new HttpEntity<>(workflowExecutionRequest, headers);
                executionResponse = restTemplate.postForObject(engineUri, entity, ExecutionResponseDTO.class);
                if (executionResponse != null){
                    Map<String , IOType> workflowOutputTypeMap = new HashMap<>();
                    workflowExecutionRequest.getWorkflow().getOutputs().forEach(workflowOutputs -> workflowOutputTypeMap.put(workflowOutputs.getName(), workflowOutputs.getType()));
                    executionResponse.setOutput_types_by_output_name(workflowOutputTypeMap);
                }
            }else{
                log.debug(ENGINE_IS_DISABLED);
                executionResponse=new ExecutionResponseDTO();
                executionResponse.setError(ENGINE_IS_DISABLED);

            }
            log.debug(executionResponse !=null ? executionResponse.toString() : "executionResponse is null!");
            return executionResponse;

        } catch (RuntimeException e) {
            log.error(e.getMessage(), e);
            throw new RuntimeEngineException("error while executing workflow", e);
        }

    }

    @Override
    public String generateCode(CodegenRequestDTO codegenRequest) {
        String code;
        log.debug("generating component code");
        log.debug(codegenRequest.toString());
        RestTemplate restTemplate = new RestTemplate();
        CodegenResponseDTO result;
        try {

            if(this.engineEnabled) {
                HttpHeaders headers = new HttpHeaders();
                if (keycloakEnabled){
                    headers.add(HttpHeaders.AUTHORIZATION, keycloakClient.getToken(keycloakUrl, keycloakRealm, engineClient, engineUser, enginePassword));
                }
                HttpEntity<CodegenRequestDTO> entity = new HttpEntity<>(codegenRequest, headers);
                result = restTemplate.postForObject(codegenUri, entity, CodegenResponseDTO.class);
                code = result != null ? result.getCode() : "";
                log.debug("code generator response:");
                log.debug(code);
            }else{
                log.debug(ENGINE_IS_DISABLED);
                code=codegenRequest.getCode();
            }

        } catch (RestClientException e) {
            log.error(e);
            throw new RuntimeEngineException("error while generating code", e);
        }
        return code;
    }
}
