package org.hetida.designer.backend.dto.adapter;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.ZonedDateTime;

@Data
public class TimestampFilterDTO extends FilterDTO{
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSX")
    private ZonedDateTime min;
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSX")
    private ZonedDateTime max;
}
