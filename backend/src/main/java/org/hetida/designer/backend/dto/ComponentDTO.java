package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;


@Data
public class ComponentDTO extends ParentDTO {
    private List<IODTO> inputs = new ArrayList<>();
    private List<IODTO> outputs = new ArrayList<>();
    private String code;
    private List<WiringDTO> wirings;
}
