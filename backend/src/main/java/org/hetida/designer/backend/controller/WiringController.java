package org.hetida.designer.backend.controller;

import java.util.List;
import java.util.UUID;

import org.hetida.designer.backend.converter.WorkflowWiringConverter;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.model.Wiring;
import org.hetida.designer.backend.service.WiringService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.extern.log4j.Log4j2;

@Log4j2
@RestController
@RequestMapping(value = "/wirings", produces = MediaType.APPLICATION_JSON_VALUE)
public class WiringController {

    private final WiringService wiringService;
    private final WorkflowWiringConverter wiringConverter;

    public WiringController(WiringService wiringService, WorkflowWiringConverter wiringConverter) {
        this.wiringService = wiringService;
        this.wiringConverter = wiringConverter;
    }


    /**
     * Returns one Wiring
     *
     * @return WiringRootDTO List
     */
    @ApiOperation(
            value = "Returns all wirings",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WiringDTO.class,
            responseContainer = "List"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got list of adapters"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/")
    public ResponseEntity<List<WiringDTO>> getAllWirings() {
        log.info("get one wiring");
        return new ResponseEntity<>(wiringConverter.toWiringDtos(wiringService.getAll()), HttpStatus.OK);
    }

    /**
     * Create wiring
     *
     * @return WiringRootDTO the created entity
     */
    @ApiOperation(
            value = "Creates a new Wiring",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WiringDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got list of adapters"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PostMapping
    public ResponseEntity<WiringDTO> createWiring(@RequestBody WiringDTO wiringDTO) {
        log.info("create a new wiring");
        Wiring wiring = this.wiringConverter.toWiring(wiringDTO);
        WiringDTO savedWiringDTO = this.wiringConverter.toWiringDto(this.wiringService.create(wiring));
        return new ResponseEntity<>(savedWiringDTO, HttpStatus.OK);
    }

    /**
     * Update wiring
     *
     * @return WiringRootDTO the updated entity
     */
    @ApiOperation(
            value = "Updates a new Wiring",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = WiringDTO.class
    )
    @ApiResponses(
            value = {
                @ApiResponse(code = 201, message = "Successfully updated the wiring"),
                @ApiResponse(code = 404, message = "Wiring not found"),
                @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PutMapping(value ="/{id}")
    public ResponseEntity<WiringDTO> updateWiring(@PathVariable("id") UUID id, @RequestBody WiringDTO wiringDTO) {
        log.info("create a new wiring");
        wiringDTO.setId(id);
        Wiring wiring = this.wiringConverter.toWiring(wiringDTO);
        WiringDTO updatedWiringDTO = this.wiringConverter.toWiringDto(this.wiringService.update(wiring));
        return new ResponseEntity<>(updatedWiringDTO, HttpStatus.OK);
    }

}
