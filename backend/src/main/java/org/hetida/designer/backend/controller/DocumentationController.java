package org.hetida.designer.backend.controller;

import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.converter.DocumentationConverter;
import org.hetida.designer.backend.dto.DocumentationDTO;
import org.hetida.designer.backend.model.Documentation;
import org.hetida.designer.backend.service.DocumentationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.UUID;

@Log4j2
@RestController
@RequestMapping(value = "/documentations", produces = MediaType.APPLICATION_JSON_VALUE)
public class DocumentationController {

    private final DocumentationService documentationService;
    private final DocumentationConverter documentationConverter;

    public DocumentationController(DocumentationService documentationService, DocumentationConverter documentationConverter) {
        this.documentationService = documentationService;
        this.documentationConverter = documentationConverter;
    }

    /**
     * Returns the documentation with the given id
     *
     * @return DocumentationDTO Object
     */
    @ApiOperation(
            value = "Returns the documentation with the given id.",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = DocumentationDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 200, message = "Successfully got the documentation"),
                    @ApiResponse(code = 404, message = "Documentation not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @GetMapping(value = "/{id}")
    public ResponseEntity<DocumentationDTO> getDocumentationById(@PathVariable("id") UUID id) {
        log.info("get documentation {}", id);
        Documentation documentation = this.documentationService.findById(id);
        log.info("found documentation {}", id);
        log.debug(documentation.toString());
        return new ResponseEntity<>(documentationConverter.convertToDto(documentation), HttpStatus.OK);
    }


    /**
     * Updates a documentation
     */
    @ApiOperation(
            value = "Updates a documentation",
            produces = MediaType.APPLICATION_JSON_VALUE,
            response = DocumentationDTO.class
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 204, message = "Successfully updated the documentation"),
                    @ApiResponse(code = 404, message = "Documentation not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @PutMapping(value = "/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<DocumentationDTO> modifyDocumentationById(@PathVariable("id") UUID id, @Valid @RequestBody DocumentationDTO documentationDto) {
        log.info("modify documentation {}", id);
        log.debug(documentationDto.toString());
        Documentation documentation = documentationConverter.convertToEntity(documentationDto);
        this.documentationService.update(documentation);
        return new ResponseEntity<>(documentationDto, HttpStatus.OK);


    }

    /**
     * Deletes a documentation
     */
    @ApiOperation(
            value = "Deletes a documentation"
    )
    @ApiResponses(
            value = {
                    @ApiResponse(code = 204, message = "Successfully deleted the documentation"),
                    @ApiResponse(code = 404, message = "Documentation not found"),
                    @ApiResponse(code = 503, message = "Internal server error")
            }
    )
    @DeleteMapping(value = "/{id}")
    public ResponseEntity<DocumentationDTO> deleteDocumentation(@PathVariable UUID id) {
        log.info("delete documentation {}", id);
        this.documentationService.delete(id);
        log.info("deleted documentation {}", id);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }
}
