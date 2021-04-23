package org.hetida.designer.backend.controller;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.NoArgsConstructor;
import lombok.extern.log4j.Log4j2;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@Log4j2
@CrossOrigin
@RestController
@RequestMapping(value = "/info", produces = MediaType.APPLICATION_JSON_VALUE)
public class InfoController {

    public InfoController(){}

    /**
     * Returns the list of  adapters
     *
     * @return Map
     */
    @ApiOperation(
            value = "Returns s sign of life",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = Map.class,
            responseContainer = "Map"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got a sign of life"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping
    public ResponseEntity<HashMap<String, String>> getInfo() {
        log.info("get sign of life");
        HashMap<String, String> map = new HashMap<>();
        map.put("msg", "Here I am");
        return new ResponseEntity<>(map, HttpStatus.OK);
    }

}
