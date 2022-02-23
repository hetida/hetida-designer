package org.hetida.designer.backend.dto;


import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class BaseItemDTO extends ParentDTO {

    private List<IODTO> inputs = new ArrayList<>();
    private List<IODTO> outputs = new ArrayList<>();
    private List<WiringDTO> wirings = new ArrayList<>();
}
