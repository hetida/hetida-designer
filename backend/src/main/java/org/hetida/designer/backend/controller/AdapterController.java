package org.hetida.designer.backend.controller;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.hetida.designer.backend.service.AdapterService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Log4j2
@RestController
@RequestMapping(value = "/adapters", produces = MediaType.APPLICATION_JSON_VALUE)
public class AdapterController {

    private final AdapterService adapterService;

    public AdapterController(AdapterService adapterService){
        this.adapterService = adapterService;
    }

    /**
     * Returns the list of  adapters
     *
     * @return ModulAdapterDTO List
     */
    @ApiOperation(
            value = "Returns all adapters",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = ModulAdapterDTO.class,
            responseContainer = "List"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got list of adapters"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/")
    public ResponseEntity<Iterable<ModulAdapterDTO>> getAdapter() {
        log.info("get adapters");
        return new ResponseEntity<>(adapterService.getAllInstalledAdapters(), HttpStatus.OK);
    }

}
