package org.hetida.designer.backend.repository;

import org.hetida.designer.backend.model.Documentation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface DocumentationRepository extends JpaRepository<Documentation, UUID> {
}