package org.hetida.designer.demo.adapter.dto;


import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.Data;
import org.hetida.designer.demo.adapter.enums.MetadataType;

@Data
public class MetaDataDTO {
  private String key;
  private JsonNode value;
  private MetadataType dataType;
  @JsonProperty("isSink")
  private boolean sink = false;
}
