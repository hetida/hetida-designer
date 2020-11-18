package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.List;
import java.util.UUID;

@Data
public class WiringDTO {
    private UUID id;
    private String name;
    private List<InputWiringDTO> inputWirings;
    private List<OutputWiringDTO> outputWirings;
}
