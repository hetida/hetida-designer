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
    @Column(name = "Id", columnDefinition = "uuid")
    private UUID id;

    @Column(name = "WiringId", columnDefinition = "uuid")
    private UUID wiringId;

    @Column(name = "WorkflowInputName")
    private String workflowInputName;

    @Column(name = "AdapterId")
    private String adapterId;

    @Column(name = "refid")
    private String refId;

    @Column(name = "refidtype")
    private String refIdType;

    @Column(name = "refkey")
    private String refKey;

    @Column(name = "type")
    private String type;

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL, mappedBy = "inputWiringId", orphanRemoval = true)
    private List<Filter> inputFilters = new ArrayList<>();
}
