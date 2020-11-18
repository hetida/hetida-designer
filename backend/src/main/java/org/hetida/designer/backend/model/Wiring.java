package org.hetida.designer.backend.model;

import lombok.Data;
import org.hibernate.annotations.LazyCollection;
import org.hibernate.annotations.LazyCollectionOption;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Data
@Table(name = "Wiring")
public class Wiring {
    @Id
    @Column(name = "Id")
    private UUID id;

    @Column(name = "Name")
    private String name;

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "wiringId")
    private List<InputWiring> inputWirings = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "wiringId")
    private List<OutputWiring> outputWirings = new ArrayList<>();
}
