package org.hetida.designer.backend.model;

import lombok.Data;

import javax.persistence.*;
import java.util.UUID;

@Entity
@Data
@IdClass(WiringFilterKey.class)
@Table(name = "Filter", uniqueConstraints={@UniqueConstraint(columnNames={"InputWiringId", "key"})})
public class Filter {
    @Id
    @Column(name = "InputWiringId", columnDefinition = "uuid")
    private UUID inputWiringId;

    @Id
    @Column(name = "Key")
    private String  key;

    @Column(name = "Value")
    private String  value;
}
