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
@Table(name = "InputWiring")
public class InputWiring {
    @Id
    @Column(name = "Id")
    private UUID id;

    @Column(name = "WiringId")
    private UUID wiringId;

    @Column(name = "WorkflowInputName")
    private String workflowInputName;

    @Column(name = "AdapterId")
    private String adapterId;

    @Column(name = "SourceId")
    private String sourceId;

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "inputWiringId", orphanRemoval = true)
    private List<Filter> inputFilters = new ArrayList<>();
}
