package org.hetida.designer.backend.dto.adapter;

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
