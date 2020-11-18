package org.hetida.designer.backend.controller;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.ComponentConverter;
import org.hetida.designer.backend.dto.ComponentDTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.ExecutionResponseDTO;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.exception.ComponentNotWriteableException;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.service.ComponentExecutionService;
import org.hetida.designer.backend.service.ComponentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.UUID;

@Log4j2
@RestController
@RequestMapping(value = "/components", produces = MediaType.APPLICATION_JSON_VALUE)
public class ComponentController {

    private final ComponentService componentService;
    private final ComponentConverter componentConverter;
    private final ComponentExecutionService componentExecutionService;

    public ComponentController(ComponentService componentService, ComponentConverter componentConverter,
                               ComponentExecutionService componentExecutionService) {
        this.componentService = componentService;
        this.componentConverter = componentConverter;
        this.componentExecutionService = componentExecutionService;
    }

    /**
     * Returns the component with the given id
     *
     * @return ComponentDTO Object
     */
    @ApiOperation(
            value = "Returns the component with the given id.",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = ComponentDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got the component"),
                    @ApiResponse(code = 404, message = "Component not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/{id}")
    public ResponseEntity<ComponentDTO> getComponentById(@PathVariable("id") UUID id) {
        log.info("get component {}", id);
        Component component = this.componentService.findById(id);
        log.info("found component {}", id);
        log.debug(component.toString());
        return new ResponseEntity<>(componentConverter.convertToDto(component), HttpStatus.OK);
    }

    /**
     * Creates a new component
     */
    @ApiOperation(
            value = "Creates a new component"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 201, message = "Successfully created the component"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public void createComponent(@Valid @RequestBody ComponentDTO componentDto) {
        log.info("create component");
        log.debug(componentDto.toString());
        Component component = componentConverter.convertToEntity(componentDto);
        this.componentService.create(component);
        log.debug(component.toString());
        log.info("created component");
    }

    /**
     * Deletes a component
     */
    @ApiOperation(
            value = "Deletes a component"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 204, message = "Successfully deleted the component"),
                    @ApiResponse(code = 403, message = "Component is already released"),
                    @ApiResponse(code = 404, message = "Component not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @DeleteMapping(value = "/{id}")
    public ResponseEntity<ComponentDTO> deleteComponent(@PathVariable UUID id) {
        log.info("delete component {}", id);
        this.componentService.delete(id);
        log.info("deleted component {}", id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }

     /**
     * Binds a wiring to the workflow.
     */
    @ApiOperation(
            value = "Binds a wiring to component",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = ComponentDTO.class
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
    public ResponseEntity<ComponentDTO> bindWiring(@PathVariable UUID id, @RequestBody WiringDTO wiringDTO) {
        log.info("bind wiring to component {}", id);

        ComponentDTO componentDTO = this.componentConverter.convertToDto(this.componentService.bindWiring(id, wiringDTO));

        log.info("binded wiring to component {}", id);
        return new ResponseEntity<>(componentDTO, HttpStatus.OK);
    }

    /**
     * executes a component
     */
    @ApiOperation(
            value = "Executes a component",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = ExecutionResponseDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully executed the component"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping(value = "/{id}/execute")
    @ResponseStatus(HttpStatus.OK)
    public ResponseEntity<ExecutionResponseDTO> execute(@Valid @RequestBody WiringDTO wiringDTO,
                                                        @PathVariable("id") UUID componentId,
                                                        @RequestParam(defaultValue = "false") boolean run_pure_plot_operators) {
        log.info("execute component");
        log.debug(componentId);
        ExecutionResponseDTO executionResponseDTO = this.componentExecutionService.execute(wiringDTO, componentId,run_pure_plot_operators);
        log.debug(executionResponseDTO.toString());
        log.info("component executed");
        return new ResponseEntity<>(executionResponseDTO, HttpStatus.OK);
    }

    /**
     * Updates a component
     */
    @ApiOperation(
            value = "Updates a component",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = ComponentDTO.class
    )
    @ApiResponses(
      value = {
                  @ApiResponse(code = 201, message = "Successfully updated the component"),
                  @ApiResponse(code = 403, message = "Component is already released"),
                  @ApiResponse(code = 404, message = "Component not found"),
                  @ApiResponse(code = 503, message = "Internal server error")
      }
    )
    @PutMapping(value = "/{id}")
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<ComponentDTO> modifyComponentById(@PathVariable("id") UUID id, @Valid @RequestBody ComponentDTO componentDto) {
        log.info("modify component {}", id);
        log.debug(componentDto.toString());
        Component existingComponent = this.componentService.findById(componentDto.getId());
        if (!ItemState.RELEASED.equals(existingComponent.getState())) {
            Component component = componentConverter.convertToEntity(componentDto);
            ComponentDTO updatedComponentDto = componentConverter.convertToDto(this.componentService.update(component));
            return new ResponseEntity<>(updatedComponentDto, HttpStatus.CREATED);
        } else {
            log.error("cannot update released component{}", componentDto.getId());
            throw new ComponentNotWriteableException();
        }
    }
}
