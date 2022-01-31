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
@Table(name = "workflowlink")
public class WorkflowLink {
    @Id
    @Column(name = "id", columnDefinition = "uuid")
    private UUID id;

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL)
    @OrderBy("sequenceNr ASC")
    @JoinTable(name = "workflowlink_to_point",
            joinColumns = @JoinColumn(name = "workflowlinkid"),
            inverseJoinColumns = @JoinColumn(name = "pointid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"workflowlinkid", "pointid"})}
    )
    private List<Point> path = new ArrayList<>();

    @Column(name = "fromoperator", columnDefinition = "uuid")
    private UUID fromOperator;

    @Column(name = "fromconnector", columnDefinition = "uuid")
    private UUID fromConnector;

    @Column(name = "tooperator", columnDefinition = "uuid")
    private UUID toOperator;

    @Column(name = "toconnector", columnDefinition = "uuid")
    private UUID toConnector;
}
