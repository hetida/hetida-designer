package org.hetida.designer.demo.adapter.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import javax.validation.constraints.DecimalMax;
import java.math.BigDecimal;
import java.time.Instant;

@Data
public class TimeseriesDTO {

    private String timeseriesId;

    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSX", timezone = "UTC")
    private Instant timestamp;

    @DecimalMax("999999.999999")
    private BigDecimal value;
}
