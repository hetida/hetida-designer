package org.hetida.designer.demo.adapter.dto;

import com.fasterxml.jackson.annotation.JsonAnyGetter;
import com.fasterxml.jackson.annotation.JsonAnySetter;
import lombok.Data;

import java.util.LinkedHashMap;
import java.util.Map;

@Data
public class DataFrameDTO {
    private Map<String, Object> dataframes = new LinkedHashMap<>();

    @JsonAnyGetter
    public Map<String, Object> getDataframes() {
        return dataframes;
    }

    @JsonAnySetter
    public void setDataframes(String key, Object value) {
        dataframes.put(key, value);
    }
}
