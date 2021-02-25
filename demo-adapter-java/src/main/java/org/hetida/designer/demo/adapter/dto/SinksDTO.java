package org.hetida.designer.demo.adapter.dto;

import lombok.Data;

import java.util.List;

@Data
public class SinksDTO {

    private int resultCount;
    private List<SinkDTO> sinks;
}
