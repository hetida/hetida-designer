package org.hetida.designer.backend.service.impl;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.exception.DocumentationNotFoundException;
import org.hetida.designer.backend.model.Documentation;
import org.hetida.designer.backend.repository.DocumentationRepository;
import org.hetida.designer.backend.service.DocumentationService;
import org.springframework.stereotype.Service;

import java.util.Optional;
import java.util.UUID;

@Service
@Log4j2
public class DocumentationServiceImpl implements DocumentationService {

    private final DocumentationRepository documentationRepository;

    public DocumentationServiceImpl(DocumentationRepository documentationRepository) {
        this.documentationRepository = documentationRepository;

    }

    @Override
    public Documentation findById(UUID id) {
        Optional<Documentation> optionalComponent = this.documentationRepository.findById(id);
        return optionalComponent.orElseGet(() -> this.create(new Documentation(id)));
    }

    private Documentation create(Documentation documentation) {
        this.documentationRepository.save(documentation);
        return documentation;
    }

    @Override
    public void update(Documentation documentation) {
        this.documentationRepository.saveAndFlush(documentation);
        log.info("modified documentation {}", documentation.getId());
        log.info(documentation);
    }

    @Override
    public void delete(UUID id) {
        Optional<Documentation> optionalComponent = this.documentationRepository.findById(id);
        Documentation documentation = optionalComponent.orElseThrow(DocumentationNotFoundException::new);
        this.documentationRepository.delete(documentation);
        log.info("deleted documentation {}", id);
    }
}
