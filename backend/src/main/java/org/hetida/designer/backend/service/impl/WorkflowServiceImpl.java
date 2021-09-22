package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.apache.commons.collections4.IterableUtils;
import org.hetida.designer.backend.converter.WorkflowConverter;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.WorkflowDTO;
import org.hetida.designer.backend.dto.WorkflowSummaryDTO;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.exception.WorkflowNotFoundException;
import org.hetida.designer.backend.exception.WorkflowNotWriteableException;
import org.hetida.designer.backend.model.*;
import org.hetida.designer.backend.repository.WiringRepository;
import org.hetida.designer.backend.repository.WorkflowRepository;
import org.hetida.designer.backend.service.ComponentService;
import org.hetida.designer.backend.service.WorkflowService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.*;

@Service
@Log4j2
public class WorkflowServiceImpl implements WorkflowService {
    private static final int INPUT_OFFSET = -200;
    private static final int OUTPUT_OFFSET = 200;
    private final WorkflowRepository workflowRepository;
    private final WorkflowConverter workflowConverter;
    private final ComponentService componentService;
    private final WiringRepository wiringRepository;

    public WorkflowServiceImpl(WorkflowRepository workflowRepository, ComponentService componentService,
            WorkflowConverter workflowConverter, WiringRepository wiringRepository) {
        this.workflowRepository = workflowRepository;
        this.componentService = componentService;
        this.workflowConverter = workflowConverter;
        this.wiringRepository = wiringRepository;
    }

    @Override
    public List<WorkflowSummaryDTO> summarizeAll() {
        List<WorkflowSummaryDTO> summaryDTOList = new ArrayList<>();
        List<Workflow> workflowList = findAll();

        workflowList.forEach(workflow -> summaryDTOList.add(this.workflowConverter.convertToSummaryDto(workflow)));

        return summaryDTOList;
    }

    @Override
    public Workflow findById(UUID id) {
        log.info("find workflow by id: {}", id);
        Optional<Workflow> optionalWorkflow = workflowRepository.findById(id);
        return  optionalWorkflow.orElseThrow(WorkflowNotFoundException::new);
    }

    @Override
    public Workflow create(Workflow workflow) {
        this.workflowRepository.save(workflow);
        return workflow;
    }

    @Override
    public Workflow update(Workflow workflow) {
        Workflow currentWorkflow = workflowRepository.findById(workflow.getId())
          .orElseThrow(WorkflowNotFoundException::new);

        validateWorkflowLinks(workflow);
        checkOperatorNamesUnique(workflow);

        workflow.setInputs(this.computeWorkflowInputs(workflow));
        workflow.setOutputs(this.computeWorkflowOutputs(workflow));

        this.workflowRepository.save(workflow);
        this.workflowRepository.deleteOrphanedData();
        log.info("modified workflow {}", workflow.getId());
        return workflow;
    }


  /**
   * Validates all WorkflowLinks inside a Workflow and checks, that all referenced WorkflowOperator exists.
   * If the WorkflowOperator not exists, the WorkflowLink will be removed from the Workflow.
   * This is a workaround for https://github.com/hetida/hetida-designer/issues/6
   * @param workflow The Workflow to check
   */
  private void validateWorkflowLinks(Workflow workflow) {
      List<WorkflowOperator> workflowOperators = workflow.getWorkflowOperators();

      List<WorkflowIO> workflowIOS =workflow.getInputs();
      workflowIOS.addAll(workflow.getOutputs());

      List <WorkflowLink> workflowLinks = workflow.getLinks();
      List <WorkflowLink> workflowLinksToRemove = new ArrayList<>();

      for(WorkflowLink workflowLink: workflowLinks) {
        if(workflowOperators.stream().noneMatch(x -> x.getId().equals(workflowLink.getFromOperator())) &&
          workflowIOS.stream().noneMatch(x -> x.getOperator().equals(workflowLink.getToOperator()))){
          log.error("Invalid workflowLink. Operator does not exist. id: {} fromOperator: {}",
            workflowLink.getId(), workflowLink.getFromOperator());
          workflowLinksToRemove.add(workflowLink);
          continue;
        }

        if(workflowOperators.stream().noneMatch(x -> x.getId().equals(workflowLink.getToOperator())) &&
          workflowIOS.stream().noneMatch(x -> x.getOperator().equals(workflowLink.getFromOperator()))){
          log.error("Invalid workflowLink. Operator does not exist. id: {} toOperator: {}",
            workflowLink.getId(), workflowLink.getToOperator());
          workflowLinksToRemove.add(workflowLink);
        }
      }
      workflow.getLinks().removeAll(workflowLinksToRemove);
    }

  private void checkOperatorNamesUnique(Workflow workflow) {
        // group operators by itemId
        Map<UUID, List<WorkflowOperator>> operatorGroups = new HashMap<>();
        if (workflow.getWorkflowOperators() != null) {
            for (WorkflowOperator currentOperator : workflow.getWorkflowOperators()) {
                if (!operatorGroups.containsKey(currentOperator.getItemId())) {
                    operatorGroups.put(currentOperator.getItemId(), new ArrayList<>());
                }
                operatorGroups.get(currentOperator.getItemId()).add(currentOperator);
            }
        }
        // check each group of operators individually
        for (List<WorkflowOperator> operatorGroup : operatorGroups.values()) {
            Map<String, WorkflowOperator> operatorMap = new HashMap<>();

            for (WorkflowOperator currentOperator : operatorGroup) {
                int suffix = 1;
                String currentOperatorName = currentOperator.getName();
                while (operatorMap.containsKey(currentOperatorName)) {
                    suffix++;
                    currentOperatorName = currentOperator.getName() + " (" + suffix + ")";
                }
                operatorMap.put(currentOperatorName, currentOperator);
                currentOperator.setName(currentOperatorName);
            }

        }
    }

    private List<WorkflowIO> computeWorkflowInputs(Workflow workflow) {
        List<WorkflowIO> ios = new ArrayList<>();
        for (WorkflowOperator currentOperator : workflow.getWorkflowOperators()) {
            if (ItemType.COMPONENT.equals(currentOperator.getType())) {
                Component componentItem = this.componentService.findById(currentOperator.getItemId());
                for (BaseIO io : componentItem.getInputs()) {
                    // search all workflow links and check if there ist one using this io as target
                    if (this.isUnused(currentOperator.getId(), io.getId(), workflow)) {
                        WorkflowIO wfIO = workflow.getInputs().stream()
                                .filter(x -> x.getOperator().equals(currentOperator.getId())
                                        && x.getConnector().equals(io.getId()))
                                .findFirst().orElse(new WorkflowIO(io.getType(), currentOperator.getId(), io.getId(),
                                        io.getPosX() + INPUT_OFFSET, io.getPosY()));
                        ios.add(wfIO);
                    }
                }

            } else {
              Workflow workflowItem = this.findById(currentOperator.getItemId());
              for (WorkflowIO io : workflowItem.getInputs()) {
                // search all workflow links and check if there ist one using this io as target
                // OR if it has a constant value
                if (!io.isConstant() && this.isUnused(currentOperator.getId(), io.getId(), workflow)) {
                  WorkflowIO wfIO = workflow.getInputs().stream().filter(x -> x.getOperator().equals(currentOperator.getId())
                      && x.getConnector().equals(io.getId())).findFirst().orElse(new WorkflowIO(io.getType(), currentOperator.getId(),
                      io.getId(), io.getPosX() + INPUT_OFFSET, io.getPosY()));
                  ios.add(wfIO);
                }
              }
            }
        }
        return ios;
    }

    private boolean isUnused(UUID operator, UUID connector, Workflow workflow) {
        if (workflow.getLinks() != null) {
            for (WorkflowLink currentLink : workflow.getLinks()) {
                if (currentLink.getToOperator().equals(operator) && currentLink.getToConnector().equals(connector)
                        && !currentLink.getFromOperator().equals(workflow.getId())) {
                    return false;
                }
            }
        }
        return true;
    }

    private List<WorkflowIO> computeWorkflowOutputs(Workflow workflow) {
        List<WorkflowIO> ios = new ArrayList<>();
        for (WorkflowOperator currentOperator : workflow.getWorkflowOperators()) {
            if (ItemType.COMPONENT.equals(currentOperator.getType())) {
                Component component = this.componentService.findById(currentOperator.getItemId());

                for (BaseIO io : component.getOutputs()) {
                    // search all workflow links and check if there ist one using this io as source
                    if (this.outputIsUnused(currentOperator.getId(), io.getId(), workflow)) {
                        WorkflowIO wfIO = workflow.getOutputs().stream()
                                .filter(x -> x.getOperator().equals(currentOperator.getId())
                                        && x.getConnector().equals(io.getId()))
                                .findFirst().orElse(new WorkflowIO(io.getType(), currentOperator.getId(), io.getId(),
                                        io.getPosX() + OUTPUT_OFFSET, io.getPosY()));
                        ios.add(wfIO);
                    }
                }
            } else {
                Workflow workflowItem = this.findById(currentOperator.getItemId());
                for (BaseIO io : workflowItem.getOutputs()) {
                    // search all workflow links and check if there ist one using this io as target
                    if (this.outputIsUnused(currentOperator.getId(), io.getId(), workflow)) {
                        WorkflowIO wfIO = workflow.getOutputs().stream()
                                .filter(x -> x.getOperator().equals(currentOperator.getId())
                                        && x.getConnector().equals(io.getId()))
                                .findFirst().orElse(new WorkflowIO(io.getType(), currentOperator.getId(), io.getId(),
                                        io.getPosX() + OUTPUT_OFFSET, io.getPosY()));
                        ios.add(wfIO);
                    }
                }
            }

        }
        return ios;
    }

    private boolean outputIsUnused(UUID operator, UUID connector, Workflow workflow) {
        if (workflow.getLinks() != null) {
            for (WorkflowLink currentLink : workflow.getLinks()) {
                if (currentLink.getFromOperator().equals(operator) && currentLink.getFromConnector().equals(connector)
                        && !currentLink.getToOperator().equals(workflow.getId())) {
                    return false;
                }
            }
        }
        return true;
    }

    @Override
    public void delete(UUID id) {
        Optional<Workflow> optionalWorkflow = this.workflowRepository.findById(id);
        Workflow workflow = optionalWorkflow.orElseThrow(WorkflowNotFoundException::new);

        if (!ItemState.RELEASED.equals(workflow.getState())) {
            this.workflowRepository.delete(workflow);
            log.info("deleted workflow {}", id);
        } else {
            log.error("cannot delete released workflow {}", id);
            throw new WorkflowNotWriteableException();
        }
    }

    @Override
    public List<WorkflowOperator> getWorkflowOperatorsRecursive(Workflow workflow) {
        List<WorkflowOperator> workflowOperators = new ArrayList<>();
        if (workflow.getWorkflowOperators() != null) {
            for (WorkflowOperator currentWorkflowOperator : workflow.getWorkflowOperators()) {
                workflowOperators.add(currentWorkflowOperator);
                if (ItemType.WORKFLOW.equals(currentWorkflowOperator.getType())) {
                    Workflow childWorkflow = this.findById(currentWorkflowOperator.getItemId());
                    workflowOperators.addAll(this.getWorkflowOperatorsRecursive(childWorkflow));
                }
            }
        }
        return workflowOperators;
    }

    @Override
    public Map<UUID, Component> getAllComponents(List<WorkflowOperator> workflowOperators) {
        List<UUID> uuids = this.filterItemIDsByOperatorType(workflowOperators, ItemType.COMPONENT);
        Map<UUID, Component> components = this.componentService.findAllById(uuids);
        components.values().forEach(component -> {
            // reset uuid for draft components
            if (ItemState.DRAFT.equals(component.getState())) {
                component.setId(UUID.randomUUID());
            }
        });
        return components;
    }

    @Override
    public Map<UUID, Workflow> getAllWorkflows(List<WorkflowOperator> workflowOperators) {
        List<UUID> uuids = this.filterItemIDsByOperatorType(workflowOperators, ItemType.WORKFLOW);
        return this.findAllById(uuids);
    }

    @Override
    public WorkflowDTO dtoById(UUID id) {
        Workflow workflow = this.findById(id);
        Map<UUID, Component> allComponents = this.getAllComponents(workflow.getWorkflowOperators());
        log.info("allComponents {}", allComponents.size());
        Map<UUID, Workflow> allWorkflows = this.getAllWorkflows(workflow.getWorkflowOperators());
        log.info("allWorkflows {}", allWorkflows.size());
        log.info("found workflow {}", id);
        log.debug(workflow.toString());
        return this.workflowConverter.convertToDto(workflow, allComponents, allWorkflows);
    }

    @Override
    public void bindWiring(UUID id, WiringDTO wiringDto) {
        Optional<Workflow> optionalWorkflow = this.workflowRepository.findById(id);
        Optional<Wiring> wiring = this.wiringRepository.findById(wiringDto.getId());

        if(!wiring.isPresent()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
        log.info("Bind Wiring to Workflow {}", id);
        log.info("WiringID: {}", wiringDto.getId());
        if(optionalWorkflow.isPresent()) {
            Workflow workflow = optionalWorkflow.get();
            Optional<Wiring> anyWiringWithId = workflow.getWirings().stream().filter(w -> w.getId().equals(wiringDto.getId())).findAny();
            log.info("Number of wiring for workflow: {}", workflow.getWirings().size());
            log.info("Wiring binding exists: {}", anyWiringWithId.isPresent());
            if (!anyWiringWithId.isPresent()){
                log.info("Adding wiring to workflow");
                workflow.getWirings().add(wiring.get());
                workflowRepository.save(workflow);
            }
        } else {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
    }

    private List<UUID> filterItemIDsByOperatorType(List<WorkflowOperator> workflowOperators, ItemType type) {
        log.info("filtering {} operators", workflowOperators.size());
        List<UUID> uuids = new ArrayList<>();
        for (WorkflowOperator workflowOperator : workflowOperators) {
            if (workflowOperator.getType().equals(type)) {
                uuids.add(workflowOperator.getItemId());
            }
        }
        return uuids;
    }

    private List<Workflow> findAll() {
        Iterable<Workflow> workflows = this.workflowRepository.findAll();
        return IterableUtils.toList(workflows);
    }

    private Map<UUID, Workflow> findAllById(List<UUID> uuids) {

        Map<UUID, Workflow> workflowMap = new HashMap<>();
        List<Workflow> workflows = this.workflowRepository.findAllById(uuids);
        if (workflows != null) {
            for (Workflow workflow : workflows) {
                workflowMap.put(workflow.getId(), workflow);
            }
        }
        return workflowMap;
    }
}
