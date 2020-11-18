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
@Table(name = "Component")
public class Component {

    @Id
    @Column(name = "id")
    private UUID id;

    @Column(name = "groupid")
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
    @JoinTable(name = "componentinput_to_componentio",
            joinColumns = @JoinColumn(name = "componentid"),
            inverseJoinColumns = @JoinColumn(name = "componentioid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"componentid", "componentioid"})}
    )
    private List<ComponentIO> inputs = new ArrayList<>();

    @LazyCollection(LazyCollectionOption.FALSE)
    @OneToMany(cascade = CascadeType.ALL)
    @OrderBy("name ASC")
    @JoinTable(name = "componentoutput_to_componentio",
            joinColumns = @JoinColumn(name = "componentid"),
            inverseJoinColumns = @JoinColumn(name = "componentioid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"componentid", "componentioid"})}
    )
    private List<ComponentIO> outputs = new ArrayList<>();

    @Column(name = "code", columnDefinition = "TEXT")
    private String code;

    @Column(name = "functionname")
    private String function_name = "main";

    @LazyCollection(LazyCollectionOption.FALSE)
    @ManyToMany(cascade = CascadeType.ALL)
    @JoinTable(name = "componentwiring",
            joinColumns = @JoinColumn(name = "componentid"),
            inverseJoinColumns = @JoinColumn(name = "wiringid"),
            uniqueConstraints = {@UniqueConstraint(columnNames = {"componentid", "wiringid"})}
    )
    private List<Wiring> wirings = new ArrayList<>();
}
