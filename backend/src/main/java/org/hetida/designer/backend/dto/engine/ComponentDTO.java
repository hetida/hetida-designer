package org.hetida.designer.backend.dto.engine;

import lombok.Data;
import org.hetida.designer.backend.dto.IODTO;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Data
public class ComponentDTO {
    public UUID uuid;
    public List<IODTO> inputs = new ArrayList<>();
    public List<IODTO> outputs = new ArrayList<>();
    public UUID code_module_uuid;
    public String function_name = "main";
}
