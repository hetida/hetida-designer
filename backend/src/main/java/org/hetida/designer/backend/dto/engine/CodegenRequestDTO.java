package org.hetida.designer.backend.dto.engine;

import lombok.Data;
import org.hetida.designer.backend.dto.IODTO;

import java.util.ArrayList;
import java.util.List;

@Data
public class CodegenRequestDTO {
    private String code;
    private List<IODTO> inputs = new ArrayList<>();
    private List<IODTO> outputs = new ArrayList<>();
    private String name;
    private String description;
    private String category;
}
