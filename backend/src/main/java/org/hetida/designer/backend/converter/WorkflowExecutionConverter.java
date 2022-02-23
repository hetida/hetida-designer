package org.hetida.designer.backend.converter;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.*;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.exception.ComponentNotFoundException;
import org.hetida.designer.backend.exception.ExecutionRequestException;
import org.hetida.designer.backend.exception.WorkflowNotFoundException;
import org.hetida.designer.backend.model.*;
import org.springframework.stereotype.Component;

import java.util.*;

@Component
@Log4j2
public class WorkflowExecutionConverter {

    private static final String ENGINE = "plain";

    private final IOConverter iOConverter;
    private final WorkflowWiringConverter workflowWiringConverter;


    public WorkflowExecutionConverter(IOConverter iOConverter, WorkflowWiringConverter workflowWiringConverter) {
        this.iOConverter = iOConverter;
        this.workflowWiringConverter = workflowWiringConverter;
    }

    private static String getIOName(UUID operatorId, UUID connectorId, List<WorkflowOperator> workflowOperators, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        String ioName = null;

        //find operator
        log.info("operators:" + workflowOperators.size());
        log.info("search for:" + operatorId);
        for (WorkflowOperator operator : workflowOperators) {
            log.info(operator.getId());

            if (operator.getId().equals(operatorId)) {
                if (ItemType.WORKFLOW.equals(operator.getType())) {
                    if (allWorkflows.containsKey(operator.getItemId())) {
                        Workflow workflow = allWorkflows.get(operator.getItemId());
                        BaseIO io = findIOById(connectorId, workflow.getInputs());
                        if (io == null) {
                            io = findIOById(connectorId, workflow.getOutputs());
                        }
                        if (io != null) {
                            ioName = io.getName();
                        } else {
                            throw new ExecutionRequestException();
                        }

                    } else {
                        throw new ExecutionRequestException();
                    }

                } else if (ItemType.COMPONENT.equals(operator.getType())) {
                    if (allComponents.containsKey(operator.getItemId())) {
                        org.hetida.designer.backend.model.Component component = allComponents.get(operator.getItemId());
                        BaseIO io = findIOById(connectorId, component.getInputs());
                        if (io == null) {
                            io = findIOById(connectorId, component.getOutputs());
                        }
                        if (io != null) {
                            ioName = io.getName();
                        } else {
                            throw new ExecutionRequestException();
                        }
                    } else {
                        throw new ExecutionRequestException();
                    }

                }
                break;
            }
        }
        if (ioName == null) {
            throw new ExecutionRequestException();
        }


        return ioName;
    }

    private static BaseIO findIOById(UUID ioId, List<? extends BaseIO> ioList) {
        log.info("search for io :" + ioId);
        for (BaseIO io : ioList) {
            log.info("- :" + io.getId());
            if (io.getId().equals(ioId)) {
                return io;
            }
        }
        return null;
    }

    public ExecutionRequestDTO convertComponentExecutionRequestDtoToExecutionRequestDto(
            WiringDTO wiringDTO, org.hetida.designer.backend.model.Component component, boolean runPurePlotOperators) {

        ExecutionRequestDTO executionRequest = new ExecutionRequestDTO();

        Map<UUID, org.hetida.designer.backend.model.Component> allComponents = new HashMap<>();
        allComponents.put(component.getId(), component);

        Map<UUID, Workflow> allWorkflows = new HashMap<>();
        //create temporary workflow
        Workflow tempWorkflow = new Workflow();
        tempWorkflow.setId(UUID.randomUUID());
        //create temporary operator
        WorkflowOperator tempOperator = new WorkflowOperator();
        tempOperator.setId(UUID.randomUUID());
        tempOperator.setItemId(component.getId());
        tempOperator.setName(component.getName());
        tempOperator.setType(ItemType.COMPONENT);
        tempWorkflow.getWorkflowOperators().add(tempOperator);
        //map all inputs and outputs
        //inputs
        if (component.getInputs() != null) {
            for (ComponentIO componentIO : component.getInputs()) {
                WorkflowIO workflowIO = new WorkflowIO();
                workflowIO.setId(UUID.randomUUID());
                workflowIO.setOperator(tempOperator.getId());
                workflowIO.setConnector(componentIO.getId());
                workflowIO.setName(componentIO.getName());
                workflowIO.setType(componentIO.getType());
                tempWorkflow.getInputs().add(workflowIO);
            }
        }
        //outputs
        if (component.getOutputs() != null) {
            for (ComponentIO componentIO : component.getOutputs()) {
                WorkflowIO workflowIO = new WorkflowIO();
                workflowIO.setId(UUID.randomUUID());
                workflowIO.setOperator(tempOperator.getId());
                workflowIO.setConnector(componentIO.getId());
                workflowIO.setName(componentIO.getName());
                workflowIO.setType(componentIO.getType());
                tempWorkflow.getOutputs().add(workflowIO);
            }
        }
        allWorkflows.put(tempWorkflow.getId(), tempWorkflow);
        executionRequest.setCode_modules(convertComponentsToCodeModuleDTOs(allComponents.values()));
        executionRequest.setComponents(convertComponentsToComponentDTOs(allComponents.values()));
        executionRequest.setConfiguration(convertExecutionDTOToConfigurationDTO(component.getId(), runPurePlotOperators));
        executionRequest.setWorkflow(this.convertWorkflowToWorkflowNodeDTO(UUID.randomUUID(), tempWorkflow, allWorkflows, allComponents));
        executionRequest.setWorkflow_wiring(workflowWiringConverter.convertWorkflowWiringDTO(wiringDTO));
        return executionRequest;
    }



    public ExecutionRequestDTO convertExecutionRequestDtoToExecutionRequestDto(
            WiringDTO wiringDTO, UUID workflowId, Map<UUID, org.hetida.designer.backend.model.Component> allComponents,
            Map<UUID, Workflow> allWorkflows, boolean runPurePlotOperators) {
        ExecutionRequestDTO executionRequest = new ExecutionRequestDTO();
        executionRequest.setWorkflow_wiring(workflowWiringConverter.convertWorkflowWiringDTO(wiringDTO));
        if (allComponents != null) {
            executionRequest.setCode_modules(convertComponentsToCodeModuleDTOs(allComponents.values()));
            executionRequest.setComponents(convertComponentsToComponentDTOs(allComponents.values()));
            executionRequest.setConfiguration(convertExecutionDTOToConfigurationDTO(workflowId, runPurePlotOperators));

            if (allWorkflows.containsKey(workflowId)) {
                Workflow workflow = allWorkflows.get(workflowId);
                executionRequest.setWorkflow(this.convertWorkflowToWorkflowNodeDTO(UUID.randomUUID(), workflow, allWorkflows, allComponents));
            } else {
                throw new WorkflowNotFoundException();
            }
            return executionRequest;
        }
        return executionRequest;
    }

    public ConfigurationDTO convertConfigurationDTO(org.hetida.designer.backend.dto.ConfigurationDTO configurationDTO) {
        ConfigurationDTO result = new ConfigurationDTO();
        result.setName(configurationDTO.getName());
        result.setEngine(configurationDTO.getEngine());
        result.setRun_pure_plot_operators(configurationDTO.isRun_pure_plot_operators());
        return result;
    }

    private CodeModuleDTO convertComponentToCodeModuleDTO(org.hetida.designer.backend.model.Component component) {
        CodeModuleDTO codeModuleDTO = new CodeModuleDTO();

        codeModuleDTO.setUuid(component.getId());

        codeModuleDTO.setCode(component.getCode());
        return codeModuleDTO;
    }

    private List<CodeModuleDTO> convertComponentsToCodeModuleDTOs(Collection<org.hetida.designer.backend.model.Component> components) {
        List<CodeModuleDTO> codeModuleDTOS = new ArrayList<>();
        if (components != null) {
            for (org.hetida.designer.backend.model.Component component : components) {
                codeModuleDTOS.add(this.convertComponentToCodeModuleDTO(component));
            }
        }
        return codeModuleDTOS;
    }

    private ComponentDTO convertComponentToComponentDTO(org.hetida.designer.backend.model.Component component) {
        ComponentDTO componentDTO = new ComponentDTO();
        componentDTO.setUuid(component.getId());
        componentDTO.setInputs(this.iOConverter.convertComponentIOToIODtos(component.getInputs()));
        componentDTO.setOutputs(this.iOConverter.convertComponentIOToIODtos(component.getOutputs()));
        componentDTO.setCode_module_uuid(component.getId());
        return componentDTO;
    }

    private List<ComponentDTO> convertComponentsToComponentDTOs(Collection<org.hetida.designer.backend.model.Component> components) {
        List<ComponentDTO> componentDTOS = new ArrayList<>();
        if (components != null) {
            for (org.hetida.designer.backend.model.Component component : components) {
                componentDTOS.add(this.convertComponentToComponentDTO(component));
            }
        }
        return componentDTOS;
    }

    private ConfigurationDTO convertExecutionDTOToConfigurationDTO(UUID id, boolean runPurePlotOperators) {
        ConfigurationDTO configurationDTO = new ConfigurationDTO();
        configurationDTO.setName(id);
        configurationDTO.setEngine(ENGINE);
        configurationDTO.setRun_pure_plot_operators(runPurePlotOperators);
        return configurationDTO;
    }

    private WorkflowNodeDTO convertWorkflowToWorkflowNodeDTO(UUID id, Workflow workflow, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        WorkflowNodeDTO workflowNodeDTO = new WorkflowNodeDTO();
        workflowNodeDTO.setId(id);
        workflowNodeDTO.setInputs(this.convertWorkflowIOToWorkflowNodeIODtos(workflow.getInputs(), workflow.getWorkflowOperators(), allWorkflows, allComponents));
        workflowNodeDTO.setOutputs(this.convertWorkflowIOToWorkflowNodeIODtos(workflow.getOutputs(), workflow.getWorkflowOperators(), allWorkflows, allComponents));
        workflowNodeDTO.setConnections(this.convertWorkflowLinksToConnectionDTOs(workflow.getLinks(), workflow.getWorkflowOperators(), allWorkflows, allComponents));
        workflowNodeDTO.setSub_nodes(this.convertWorkflowOperatorsToSubNodes(workflow.getWorkflowOperators(), allWorkflows, allComponents));
        return workflowNodeDTO;
    }

    private WorkflowNodeIODTO convertToWorkflowNodeIODto(WorkflowIO entity, List<WorkflowOperator> workflowOperators, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        WorkflowNodeIODTO ioDTO = new WorkflowNodeIODTO();
        ioDTO.setType(entity.getType());
        ioDTO.setName(entity.getName());
        ioDTO.setId(entity.getId());
        ioDTO.setPosX(entity.getPosX());
        ioDTO.setPosY(entity.getPosY());
        ioDTO.setId_of_sub_node(entity.getOperator());
        ioDTO.setName_in_subnode(getIOName(entity.getOperator(), entity.getConnector(), workflowOperators, allWorkflows, allComponents));
        ioDTO.setConstant(entity.isConstant());
        ioDTO.setConstantValue(entity.getConstantValue());
        return ioDTO;
    }

    private List<WorkflowNodeIODTO> convertWorkflowIOToWorkflowNodeIODtos(final List<WorkflowIO> entities, List<WorkflowOperator> workflowOperators, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        List<WorkflowNodeIODTO> workflowNodeIODTOs = new ArrayList<>();
        log.info("convertWorkflowIOToWorkflowNodeIODtos");
        if (entities != null) {
            log.info("io count:" + entities.size());
            for (WorkflowIO workflowIO : entities) {
                WorkflowNodeIODTO current = this.convertToWorkflowNodeIODto(workflowIO, workflowOperators, allWorkflows, allComponents);
                workflowNodeIODTOs.add(current);
            }
        }
        return workflowNodeIODTOs;
    }

    private ConnectionDTO convertWorkflowLinkToConnectionDTO(WorkflowLink workflowLink, List<WorkflowOperator> workflowOperators, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {

        //TODO: find better solution for outer workflow IO handling
        WorkflowOperator from = workflowOperators.stream().filter(op -> op.getId().equals(workflowLink.getFromOperator())).findFirst().orElse(null);
        WorkflowOperator to = workflowOperators.stream().filter(op -> op.getId().equals(workflowLink.getToOperator())).findFirst().orElse(null);


        if (from != null && to != null) {
            ConnectionDTO connectionDTO = new ConnectionDTO();
            connectionDTO.setOutput_in_workflow_id(workflowLink.getToOperator());
            connectionDTO.setOutput_id(workflowLink.getToConnector());
            connectionDTO.setOutput_name(getIOName(workflowLink.getToOperator(), workflowLink.getToConnector(), workflowOperators, allWorkflows, allComponents));
            connectionDTO.setInput_in_workflow_id(workflowLink.getFromOperator());
            connectionDTO.setInput_id(workflowLink.getFromConnector());
            connectionDTO.setInput_name(getIOName(workflowLink.getFromOperator(), workflowLink.getFromConnector(), workflowOperators, allWorkflows, allComponents));
            return connectionDTO;
        } else {
            return null;
        }
    }

    private List<ConnectionDTO> convertWorkflowLinksToConnectionDTOs(Collection<WorkflowLink> workflowLinks, List<WorkflowOperator> workflowOperators, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        List<ConnectionDTO> connectionDTOs = new ArrayList<>();
        log.info("convertWorkflowLinksToConnectionDTOs");
        if (workflowLinks != null) {
            log.info("links count:" + workflowLinks.size());
            for (WorkflowLink workflowLink : workflowLinks) {
                //TODO: better handling for outer workflow io handling
                //temporary solution: filter them out
                ConnectionDTO current = this.convertWorkflowLinkToConnectionDTO(workflowLink, workflowOperators, allWorkflows, allComponents);
                if (current != null) {
                    connectionDTOs.add(current);
                }

            }
        }
        return connectionDTOs;
    }

    private ComponentNodeDTO convertComponentToComponentNodeDTO(UUID id, org.hetida.designer.backend.model.Component component) {
        ComponentNodeDTO componentNodeDTO = new ComponentNodeDTO();
        componentNodeDTO.setComponent_uuid(component.getId());
        componentNodeDTO.setId(id);
        componentNodeDTO.setInputs(this.iOConverter.convertComponentIOToIODtos(component.getInputs()));
        componentNodeDTO.setOutputs(this.iOConverter.convertComponentIOToIODtos(component.getOutputs()));
        return componentNodeDTO;
    }

    private BaseNode convertWorkflowOperatorToSubNode(WorkflowOperator workflowOperator, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        if (ItemType.COMPONENT.equals(workflowOperator.getType())) {
            if (allComponents.containsKey(workflowOperator.getItemId())) {
                org.hetida.designer.backend.model.Component component = allComponents.get(workflowOperator.getItemId());
                return this.convertComponentToComponentNodeDTO(workflowOperator.getId(), component);
            } else {
                throw new ComponentNotFoundException();
            }
        } else {
            if (allWorkflows.containsKey(workflowOperator.getItemId())) {
                Workflow workflow = allWorkflows.get(workflowOperator.getItemId());
                return this.convertWorkflowToWorkflowNodeDTO(workflowOperator.getId(), workflow, allWorkflows, allComponents);
            } else {
                throw new WorkflowNotFoundException();
            }
        }
    }

    private List<BaseNode> convertWorkflowOperatorsToSubNodes(List<WorkflowOperator> workflowOperators, Map<UUID, Workflow> allWorkflows, Map<UUID, org.hetida.designer.backend.model.Component> allComponents) {
        List<BaseNode> subNodes = new ArrayList<>();
        if (workflowOperators != null) {
            for (WorkflowOperator workflowOperator : workflowOperators) {
                subNodes.add(this.convertWorkflowOperatorToSubNode(workflowOperator, allWorkflows, allComponents));
            }
        }
        return subNodes;
    }
}
