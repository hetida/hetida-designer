package org.hetida.designer.backend.model;

import lombok.Data;
import org.hetida.designer.backend.enums.ItemState;
import org.hibernate.annotations.LazyCollection;
import org.hibernate.annotations.LazyCollectionOption;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Data
@Table(name = "workflow")
public class Workflow {
    @Id
    @Column(name = "id", columnDefinition = "uuid")
    private UUID id;

    @Column(name = "groupid", columnDefinition = "uuid")
    private UUID groupId;

    @Column(name = "name")
    private String name;

    @Column(name = "description")
    private String description;

    @Column(name = "category")
    private String category;

    @Column(name = "tag")
    private String tag;

    @Column(name = "state")
    @Enumerated(EnumType.STRING)
    private ItemState state;

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL)
    @OrderBy("name ASC")
    @JoinTable(name = "workflowinput_to_workflowio",
            joinColumns = @JoinColumn(name = "workflowid"),
            inverseJoinColumns = @JoinColumn(name = "workflowioid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"workflowid", "workflowioid"})}
    )
    private List<WorkflowIO> inputs = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL)
    @OrderBy("name ASC")
    @JoinTable(name = "workflowoutput_to_workflowio",
            joinColumns = @JoinColumn(name = "workflowid"),
            inverseJoinColumns = @JoinColumn(name = "workflowioid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"workflowid", "workflowioid"})}
    )
    private List<WorkflowIO> outputs = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL)
    @JoinTable(name = "workflow_to_workflowoperator",
            joinColumns = @JoinColumn(name = "workflowid"),
            inverseJoinColumns = @JoinColumn(name = "workflowoperatorid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"workflowid", "workflowoperatorid"})}
    )
    private List<WorkflowOperator> workflowOperators = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @ManyToMany(cascade = CascadeType.ALL)
    @JoinTable(name = "WorkflowWiring",
            joinColumns = @JoinColumn(name = "workflowid"),
            inverseJoinColumns = @JoinColumn(name = "wiringid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"workflowid", "wiringid"})}
    )
    private List<Wiring> wirings = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL)
    @JoinTable(name = "workflow_to_workflowlink",
      joinColumns = @JoinColumn(name = "workflowid"),
      inverseJoinColumns = @JoinColumn(name = "workflowlinkid"),
      uniqueConstraints = {@UniqueConstraint(columnNames = {"workflowid", "workflowlinkid"})}
    )
    private List<WorkflowLink> links = new ArrayList<>();
}
