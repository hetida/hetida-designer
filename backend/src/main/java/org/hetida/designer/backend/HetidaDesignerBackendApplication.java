package org.hetida.designer.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import javax.annotation.PostConstruct;

@SpringBootApplication
public class HetidaDesignerBackendApplication {

    private final ObjectMapper objectMapper;

    public HetidaDesignerBackendApplication(ObjectMapper objectMapper){
        this.objectMapper = objectMapper;
    }

    public static void main(String[] args) {
        SpringApplication.run(HetidaDesignerBackendApplication.class, args);
    }

    @PostConstruct
    public void setUp() {
        objectMapper.registerModule(new JavaTimeModule());
    }

}

