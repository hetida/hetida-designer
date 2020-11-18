package org.hetida.designer.backend.listener.kafka.dto;

import lombok.Data;

import java.util.UUID;

@Data
public class ConfigurationDTO {
    public UUID name;
    public String engine;
    public boolean run_pure_plot_operators;
}
