package org.hetida.designer.backend.repository;

import org.hetida.designer.backend.model.Wiring;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface WiringRepository extends JpaRepository<Wiring, UUID> {}