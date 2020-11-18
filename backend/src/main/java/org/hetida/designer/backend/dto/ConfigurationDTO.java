package org.hetida.designer.backend.dto;

import lombok.Data;

import java.util.UUID;

@Data
public class ConfigurationDTO {
    public UUID name;
    public String engine;
    public boolean run_pure_plot_operators;
}
