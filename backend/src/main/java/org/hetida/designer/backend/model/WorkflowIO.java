package org.hetida.designer.backend.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import org.hetida.designer.backend.converter.JSONAttributeConverter;
import org.hetida.designer.backend.enums.IOType;

import javax.persistence.Column;
import javax.persistence.Convert;
import javax.persistence.Entity;
import javax.persistence.Table;
import java.util.Map;
import java.util.UUID;


@Entity
@Data
@NoArgsConstructor
@SuppressWarnings("JpaAttributeTypeInspection")
@Table(name = "workflowio")
public class WorkflowIO extends BaseIO {
    @Column(name = "operator", columnDefinition = "uuid")
    private UUID operator;

    @Column(name = "connector", columnDefinition = "uuid")
    private UUID connector;

    @Column(name = "constant")
    private boolean constant;

    @Column(name = "constantvalue")
    @Convert(converter = JSONAttributeConverter.class)
    private Map<String, Object> constantValue;

    public WorkflowIO(IOType type, UUID operator, UUID connector, int x, int y) {

        this.setType(type);
        this.setOperator(operator);
        this.setConnector(connector);
        this.setId(UUID.randomUUID());
        this.setPosX(x);
        this.setPosY(y);
    }
}
