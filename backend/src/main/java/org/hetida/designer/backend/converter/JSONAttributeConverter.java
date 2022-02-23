package org.hetida.designer.backend.converter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;

import javax.persistence.AttributeConverter;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@Log4j2
public class JSONAttributeConverter implements AttributeConverter<Map<String, Object>, String> {
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String convertToDatabaseColumn(Map<String, Object> jsonMap) {

        String jsonString = null;
        if (jsonMap != null) {
            try {

                jsonString = objectMapper.writeValueAsString(jsonMap);
            } catch (final JsonProcessingException e) {
                log.error("JSON writing error", e);
            }
        }

        return jsonString;
    }

    @Override
    public Map<String, Object> convertToEntityAttribute(String jsonString) {

        Map<String, Object> jsonMap = new HashMap<>();
        if (jsonString != null) {
            try {
                TypeReference<HashMap<String,Object>> typeRef
                        = new TypeReference<HashMap<String,Object>>() {};
                jsonMap = objectMapper.readValue(jsonString,typeRef);
            } catch (final IOException e) {
                log.error("JSON reading error", e);
                log.error(jsonString);
            }
        }
        return jsonMap;
    }

}