package org.hetida.designer.demo.adapter.dto.client;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import javax.validation.constraints.DecimalMax;
import javax.validation.constraints.DecimalMin;
import javax.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.Instant;

@Data
public class ClientTimeseriesDTO {

    private String channelId;

    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss.SSSSSSSSSX", timezone = "UTC")
    private Instant timestamp;

    @Size(max = 255)
    private String message;

    @DecimalMin("-999999.999999")
    @DecimalMax("999999.999999")
    private BigDecimal measurement;
}
