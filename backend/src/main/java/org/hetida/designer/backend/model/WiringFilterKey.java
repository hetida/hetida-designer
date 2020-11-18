package org.hetida.designer.backend.model;

import lombok.Data;
import lombok.RequiredArgsConstructor;

import java.io.Serializable;
import java.util.UUID;

@Data
@RequiredArgsConstructor
public class WiringFilterKey implements Serializable {

    private static final long serialVersionUID = -724265290247776518L;
    private UUID inputWiringId;
    private String key;
}
