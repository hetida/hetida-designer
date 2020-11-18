package org.hetida.designer.backend.dto.engine;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.time.ZonedDateTime;

@Data
public class TSFilterDTO {
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSX")
    @JsonProperty("from_timestamp")
    private ZonedDateTime fromTimestamp;
    @JsonProperty("to_timestamp")
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSX")
    private ZonedDateTime toTimestamp;
}
