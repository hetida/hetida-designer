package org.hetida.designer.backend.controller;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.BaseItemConverter;
import org.hetida.designer.backend.dto.BaseItemDTO;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.enums.ItemType;
import org.hetida.designer.backend.exception.*;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.model.Workflow;
import org.hetida.designer.backend.service.BaseItemService;
import org.hetida.designer.backend.service.ComponentService;
import org.hetida.designer.backend.service.WorkflowService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.util.UUID;

@Log4j2
@CrossOrigin
@RestController
@RequestMapping(value = "/base-items", produces = MediaType.APPLICATION_JSON_VALUE)
public class BaseItemController {


    private final BaseItemService baseItemService;
    private final BaseItemConverter baseItemConverter;

    private final ComponentService componentService;
    private final WorkflowService workflowService;


    public BaseItemController(BaseItemService baseItemService, BaseItemConverter baseItemConverter, ComponentService componentService, WorkflowService workflowService) {
        this.baseItemService = baseItemService;
        this.baseItemConverter = baseItemConverter;
        this.componentService = componentService;
        this.workflowService = workflowService;
    }

    /**
     * Returns combined list of all base items (components and workflows).
     *
     * @return List of BaseItemDTO Objects
     */
    @ApiOperation(
            value = "Returns combined list of all base items (components and workflows).",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = BaseItemDTO.class,
            responseContainer = "List"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got all base items"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping
    public ResponseEntity<Iterable<BaseItemDTO>> getAllItems() {

        return new ResponseEntity<>(this.baseItemService.getAllBaseItems(), HttpStatus.OK);

    }

    /**
     * Returns the base item with the given id
     *
     * @return BaseItemDTO Object
     */
    @ApiOperation(
            value = "Returns the base item with the given id.",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = BaseItemDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got the base item"),
                    @ApiResponse(code = 404, message = "base item not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/{id}")
    public ResponseEntity<BaseItemDTO> getItemById(@PathVariable("id") UUID id) {
        log.info("get base item {}", id);
        try {
            Component component = this.componentService.findById(id);
            log.info("found component {}", id);
            log.debug(component.toString());
            BaseItemDTO dto = baseItemConverter.convertComponentToDto(component);
            return new ResponseEntity<>(dto, HttpStatus.OK);
        } catch (ComponentNotFoundException e) {

            try {
                Workflow workflow = this.workflowService.findById(id);
                log.info("found workflow {}", id);
                log.debug(workflow.toString());
                BaseItemDTO dto = baseItemConverter.convertWorkflowToDto(workflow);
                return new ResponseEntity<>(dto, HttpStatus.OK);
            } catch (WorkflowNotFoundException e1) {
                throw new BaseItemNotFoundException();
            }
        }
    }


    /**
     * Creates a new item
     */
    @ApiOperation(
            value = "Creates a new item",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = BaseItemDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 201, message = "Successfully created the item"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<BaseItemDTO> createItem(@Valid @RequestBody BaseItemDTO itemDto) {
        log.info("create item");
        log.debug(itemDto.toString());
        if (itemDto.getType().equals(ItemType.COMPONENT)) {
            Component component = baseItemConverter.convertToComponentEntity(itemDto);
            Component created = this.componentService.create(component);
            log.debug(component.toString());
            log.info("created component");
            BaseItemDTO updatedDTO = baseItemConverter.convertComponentToDto(created);
            return new ResponseEntity<>(updatedDTO, HttpStatus.CREATED);
        } else {
            Workflow workflow = baseItemConverter.convertToWorkflowEntity(itemDto);
            Workflow created = this.workflowService.create(workflow);
            log.debug(workflow.toString());
            log.info("created workflow");
            BaseItemDTO updatedDTO = baseItemConverter.convertWorkflowToDto(created);
            return new ResponseEntity<>(updatedDTO, HttpStatus.CREATED);
        }
    }

    /**
     * Updates a item
     */
    @ApiOperation(
            value = "Updates basic attributes of a component or workflow",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = BaseItemDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 201, message = "Successfully updated the item"),
                    @ApiResponse(code = 403, message = "Item is already released"),
                    @ApiResponse(code = 404, message = "Item not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PutMapping(value = "/{id}")
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<BaseItemDTO> modifyItemById(@PathVariable("id") UUID id, @Valid @RequestBody BaseItemDTO itemDto) {
        log.info("update item {}", id);
        log.debug(itemDto.toString());
        if (itemDto.getType().equals(ItemType.COMPONENT)) {
            Component component = this.componentService.findById(itemDto.getId());
            if (ItemState.RELEASED.equals(component.getState())) {
                if (ItemState.DISABLED.equals(itemDto.getState()) && !ItemState.DISABLED.equals(component.getState())) {
                    //item is currently being released
                    component.setState(ItemState.DISABLED);
                } else {
                    log.error("cannot modify released component {}", component.getId());
                    throw new ComponentNotWriteableException();
                }

            } else {
                component = baseItemConverter.mergeToComponentEntity(itemDto, component);
            }
            Component updated = this.componentService.update(component);
            log.debug(component.toString());
            log.info("updated component");
            BaseItemDTO updatedDTO = baseItemConverter.convertComponentToDto(updated);
            return new ResponseEntity<>(updatedDTO, HttpStatus.CREATED);
        } else {
            Workflow workflow = this.workflowService.findById(itemDto.getId());
            if (ItemState.RELEASED.equals(workflow.getState())) {
                if (ItemState.DISABLED.equals(itemDto.getState()) && !ItemState.DISABLED.equals(workflow.getState())) {
                    //item is currently being released
                    workflow.setState(ItemState.DISABLED);
                } else {
                    log.error("cannot modify released workflow {}", workflow.getId());
                    throw new WorkflowNotWriteableException();
                }
            } else {
                workflow = baseItemConverter.mergeToWorkflowEntity(itemDto, workflow);
            }

            Workflow updated = this.workflowService.update(workflow);
            log.debug(workflow.toString());
            log.info("updated workflow");
            BaseItemDTO updatedDTO = baseItemConverter.convertWorkflowToDto(updated);
            return new ResponseEntity<>(updatedDTO, HttpStatus.CREATED);
        }
    }
}
