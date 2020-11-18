package org.hetida.designer.backend.repository;


import org.hetida.designer.backend.model.Component;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ComponentRepository extends JpaRepository<Component, UUID> {
    List<Component> findAllById(Iterable<UUID> ids);
}