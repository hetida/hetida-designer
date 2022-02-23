package org.hetida.designer.backend.controller;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.WorkflowConverter;
import org.hetida.designer.backend.dto.WorkflowDTO;
import org.hetida.designer.backend.dto.WorkflowSummaryDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.model.Workflow;
import org.hetida.designer.backend.service.WorkflowExecutionService;
import org.hetida.designer.backend.service.WorkflowService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;
import java.util.UUID;

@Log4j2
@RestController
@RequestMapping(value = "/workflows", produces = MediaType.APPLICATION_JSON_VALUE)
public class WorkflowController {

    private final WorkflowService workflowService;
    private final WorkflowConverter workflowConverter;
    private final WorkflowExecutionService workflowExecutionService;

    public WorkflowController(WorkflowService workflowService, WorkflowConverter workflowConverter, WorkflowExecutionService workflowExecutionService) {
        this.workflowService = workflowService;
        this.workflowConverter = workflowConverter;
        this.workflowExecutionService = workflowExecutionService;
    }

    /**
     * Returns a list of workflows
     *
     * @return WorkflowSummaryDTO List
     */
    @ApiOperation(
            value = "Returns a list of workflows",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WorkflowSummaryDTO.class,
            responseContainer = "List"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got list of workflows"),
                    @ApiResponse(code = 404, message = "No workflows found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/")
    public ResponseEntity<List<WorkflowSummaryDTO>> getAllWorkflows() {
        log.info("get workflow summaries");
        List<WorkflowSummaryDTO> workflowSummaryDTOList = this.workflowService.summarizeAll();
        return ResponseEntity.ok(workflowSummaryDTOList);
    }

    /**
     * Returns the workflow with the given id
     *
     * @return WorkflowDTO Object
     */
    @ApiOperation(
            value = "Returns the workflow with the given id.",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WorkflowDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got the workflow"),
                    @ApiResponse(code = 404, message = "Component not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/{id}")
    public ResponseEntity<WorkflowDTO> getWorkflowById(@PathVariable("id") UUID id) {
        log.info("get workflow {}", id);
        WorkflowDTO workflowDTO = this.workflowService.dtoById(id);
        return new ResponseEntity<>(workflowDTO, HttpStatus.OK);
    }


    /**
     * Creates a new workflow
     */
    @ApiOperation(
            value = "Creates a new workflow",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WorkflowDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 201, message = "Successfully created the workflow"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<WorkflowDTO> createWorkflow(@Valid @RequestBody WorkflowDTO workflowDto) {
        log.info("create workflow");
        log.debug(workflowDto.toString());
        Workflow workflow = workflowConverter.convertToEntity(workflowDto);
        Workflow saved=this.workflowService.create(workflow);
        WorkflowDTO savedWorkflowDTO = this.workflowService.dtoById(saved.getId());
        log.debug(workflow.toString());
        log.info("created workflow");
        return new ResponseEntity<>(savedWorkflowDTO, HttpStatus.CREATED);
    }

    /**
     * Deletes a workflow
     */
    @ApiOperation(
            value = "Deletes a workflow"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 204, message = "Successfully deleted the workflow"),
                    @ApiResponse(code = 403, message = "Workflow is already released"),
                    @ApiResponse(code = 404, message = "Workflow not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @DeleteMapping(value = "/{id}")
    public ResponseEntity<WorkflowDTO> deleteWorkflow(@PathVariable UUID id) {
        log.info("delete workflow {}", id);
        this.workflowService.delete(id);
        log.info("deleted workflow {}", id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }

     /**
     * Binds a wiring to the workflow. 
     */
    @ApiOperation(
            value = "Binds a wiring to the worflow",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WorkflowDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 204, message = "Successfully binded the wiring"),
                    @ApiResponse(code = 403, message = "Wiring is already bound"),
                    @ApiResponse(code = 404, message = "Wiring not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping(value = "/{id}/wirings")
    public ResponseEntity<WorkflowDTO> bindWiring(@PathVariable UUID id, @RequestBody WiringDTO wiringDto) {
        log.info("bind wiring to workflow {}", id);
        this.workflowService.bindWiring(id, wiringDto);
        log.info("binded wiring to workflow {}", id);
        return new ResponseEntity<>(this.workflowService.dtoById(id), HttpStatus.OK);
    }

    /**
     * executes a workflow
     */
    @ApiOperation(
            value = "Executes a workflow",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = ExecutionResponseDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully executed the workflow"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping(value = "/{id}/execute")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<ExecutionResponseDTO> execute(@Valid @RequestBody WiringDTO wiringDTO, @PathVariable("id")UUID workflowId, @RequestParam(defaultValue = "false") boolean run_pure_plot_operators) {
        log.info("execute workflow");
        log.debug(workflowId);
        ExecutionResponseDTO executionResponseDTO = this.workflowExecutionService.execute(wiringDTO, workflowId, run_pure_plot_operators);
        log.debug(executionResponseDTO.toString());
        log.info("workflow executed");
        return new ResponseEntity<>(executionResponseDTO, HttpStatus.OK);
    }

  /**
   * Updates a workflow
   */
  @ApiOperation(
            value = "Updates a workflow",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WorkflowDTO.class
  )
  @ApiResponses(
    value = {
                    @ApiResponse(code = 201, message = "Successfully updated the workflow"),
                    @ApiResponse(code = 403, message = "Workflow is already released"),
                    @ApiResponse(code = 404, message = "Workflow not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
    }
  )
  @PutMapping(value = "/{id}")
  @ResponseStatus(HttpStatus.CREATED)
  public ResponseEntity<WorkflowDTO> modifyWorkflowById(@PathVariable("id") UUID id, @Valid @RequestBody WorkflowDTO workflowDto) {
        log.info("modify workflow {}", id);
        log.debug(workflowDto.toString());
        Workflow workflow = workflowConverter.convertToEntity(workflowDto);
        this.workflowService.update(workflow);
        log.info("modified workflow {}", id);
        WorkflowDTO workflowDTO = this.workflowService.dtoById(id);
        return new ResponseEntity<>(workflowDTO, HttpStatus.CREATED);
  }
}
