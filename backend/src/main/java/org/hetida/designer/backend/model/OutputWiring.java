package org.hetida.designer.backend.model;

import lombok.Data;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import java.util.UUID;

@Entity
@Data
@Table(name = "OutputWiring")
public class OutputWiring {
    @Id
    @Column(name = "Id")
    private UUID id;

    @Column(name = "WiringId")
    private UUID wiringId;

    @Column(name = "WorkflowOutputName")
    private String workflowOutputName;

    @Column(name = "AdapterId")
    private String adapterId;

    @Column(name = "SinkId")
    private String sinkId;
}
