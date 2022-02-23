package org.hetida.designer.backend.listener.kafka.dto;

import lombok.Data;

import java.util.UUID;

import javax.persistence.Column;

@Data
public class ConfigurationDTO {
    @Column(columnDefinition = "uuid")
    public UUID name;

    public String engine;
    public boolean run_pure_plot_operators;
}
