package org.hetida.designer.demo.adapter.dto;

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import lombok.Data;

@Data
@JsonTypeInfo(
        use = JsonTypeInfo.Id.NAME,
        property = "dataType")
@JsonSubTypes({
        @JsonSubTypes.Type(value = TimestampFilterDTO.class, name = "timestamp")
})
public class FilterDTO {
    private String name;
    private boolean required;
}
