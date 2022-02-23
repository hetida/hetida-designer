package org.hetida.designer.backend.model;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import javax.persistence.CascadeType;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.OneToMany;
import javax.persistence.Table;

import org.hibernate.annotations.LazyCollection;
import org.hibernate.annotations.LazyCollectionOption;

import lombok.Data;

@Entity
@Data
@Table(name = "Wiring")
public class Wiring {
    @Id
    @Column(name = "Id", columnDefinition = "uuid")
    private UUID id;

    @Column(name = "Name")
    private String name;

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "wiringId")
    private List<InputWiring> inputWirings = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(orphanRemoval = true, cascade = CascadeType.ALL, mappedBy = "wiringId")
    private List<OutputWiring> outputWirings = new ArrayList<>();
}
