package org.hetida.designer.demo.adapter.dto;

import lombok.Data;

import java.util.List;

@Data
public class SourcesDTO {

    private int resultCount;
    private List<SourceDTO> sources;
}
