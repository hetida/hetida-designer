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
    @Column(name = "Id", columnDefinition = "uuid")
    private UUID id;

    @Column(name = "WiringId", columnDefinition = "uuid")
    private UUID wiringId;

    @Column(name = "WorkflowOutputName")
    private String workflowOutputName;

    @Column(name = "AdapterId")
    private String adapterId;

    @Column(name = "Refid")
    private String refId;

    @Column(name = "refidtype")
    private String refIdType;

    @Column(name = "refkey")
    private String refKey;

    @Column(name = "type")
    private String type;
}
