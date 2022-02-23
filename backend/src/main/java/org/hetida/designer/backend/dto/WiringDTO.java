package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.List;
import java.util.UUID;

import javax.persistence.Column;

@Data
public class WiringDTO {

    @Column(columnDefinition = "uuid")
    private UUID id;

    private String name;
    private List<InputWiringDTO> inputWirings;
    private List<OutputWiringDTO> outputWirings;
}
