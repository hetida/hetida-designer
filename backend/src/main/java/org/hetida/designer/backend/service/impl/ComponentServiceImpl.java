package org.hetida.designer.backend.service.impl;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.hetida.designer.backend.converter.ComponentConverter;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.dto.engine.CodegenRequestDTO;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.exception.ComponentNotFoundException;
import org.hetida.designer.backend.exception.ComponentNotWriteableException;
import org.hetida.designer.backend.model.Component;
import org.hetida.designer.backend.model.ComponentIO;
import org.hetida.designer.backend.model.Wiring;
import org.hetida.designer.backend.repository.ComponentRepository;
import org.hetida.designer.backend.repository.WiringRepository;
import org.hetida.designer.backend.service.ComponentService;
import org.hetida.designer.backend.service.EngineService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ResponseStatusException;

import lombok.extern.log4j.Log4j2;

@Service
@Log4j2
public class ComponentServiceImpl implements ComponentService {

    private final ComponentConverter componentConverter;
    private final ComponentRepository componentRepository;
    private final EngineService engineService;
    private final WiringRepository wiringRepository;

    public ComponentServiceImpl(ComponentConverter componentConverter, ComponentRepository componentRepository,
            EngineService engineService, WiringRepository wiringRepository) {
        this.componentConverter = componentConverter;
        this.componentRepository = componentRepository;
        this.engineService = engineService;
        this.wiringRepository = wiringRepository;
    }

    @Override
    public Map<UUID, Component> findAllById(List<UUID> uuids) {
        Map<UUID, Component> componentMap = new HashMap<>();
        List<Component> components = this.componentRepository.findAllById(uuids);
        if (components != null) {
            for (Component component : components) {
                componentMap.put(component.getId(), component);
            }
        }
        return componentMap;
    }

    @Override
    public Component findById(UUID id) {
        Optional<Component> optionalComponent = this.componentRepository.findById(id);
        return optionalComponent.orElseThrow(ComponentNotFoundException::new);
    }

    @Override
    public Component create(Component component) {
        if (StringUtils.isEmpty(component.getCode())) {
            component.setCode(this.generateCode(component));
        } else {
            log.debug("code generation is disabled");
        }
        this.componentRepository.save(component);
        return component;
    }

    @Override
    public Component update(Component component) {
        Component existingComponent = this.componentRepository.findById(component.getId())
                .orElseThrow(ComponentNotFoundException::new);
        log.info("updating component");
        log.info("update:");
        log.info(component.toString());

        boolean ioUpdate = isUpdateRequired(component.getInputs(), existingComponent.getInputs())
                || isUpdateRequired(component.getOutputs(), existingComponent.getOutputs());

        if (ioUpdate) {
            log.debug("component IO updated.");
        } else {
            log.debug("component IO not updated.");
        }
        component.setCode(this.generateCode(component));        
        this.componentRepository.saveAndFlush(component);
        log.info("modified component {}", component.getId());
        log.info(component);
        return component;

    }

    private String generateCode(Component component) {
        log.debug("generating component code");
        CodegenRequestDTO codegenRequest = this.componentConverter.convertToCodegenRequestDto(component);
        return this.engineService.generateCode(codegenRequest);
    }

    private boolean isUpdateRequired(List<ComponentIO> componentIO, List<ComponentIO> existingComponentIO) {
        boolean hasNewIOItems = existingComponentIO.stream().map(existingInput -> {
            ComponentIO foundComponentIO = componentIO.stream()
            .filter(input -> existingInput.getId().equals(input.getId())).findFirst().orElse(null);
            return foundComponentIO == null;
        }).reduce(false, (acc, hasChanges) -> {
            if (acc) {
                return true;
            }
            return hasChanges;
        });

        boolean hasIOChanges = componentIO.stream().map(input -> {
            ComponentIO foundExistingInput = existingComponentIO.stream()
                    .filter(existingInput -> input.getId().equals(existingInput.getId())).findFirst().orElse(null);
            if (foundExistingInput == null) {
                return true;
            }
            boolean nameHasChanged = !foundExistingInput.getName().equals(input.getName());
            boolean typeHasChanged = !foundExistingInput.getType().equals(input.getType());
            return nameHasChanged || typeHasChanged;
        }).reduce(false, (acc, hasChanges) -> {
            if (acc) {
                return true;
            }
            return hasChanges;
        });

        return hasIOChanges || hasNewIOItems;
    }

    @Override
    public void delete(UUID id) {
        Optional<Component> optionalComponent = this.componentRepository.findById(id);
        Component component = optionalComponent.orElseThrow(ComponentNotFoundException::new);

        if (!ItemState.RELEASED.equals(component.getState())) {
            this.componentRepository.delete(component);
            log.info("deleted component {}", id);
        } else {
            log.error("cannot delete released component{}", id);
            throw new ComponentNotWriteableException();
        }
    }

    @Override
    public Component bindWiring(UUID id, WiringDTO wiringDto) {
        Optional<Component> optionalComponent = this.componentRepository.findById(id);
        Optional<Wiring> optionalWiring = this.wiringRepository.findById(wiringDto.getId());
        
        Wiring wiring = optionalWiring.orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Wiring not found"));
        log.info("Bind Wiring to Component {}", id);
        log.info("WiringID: {}", wiringDto.getId());
        Component component = optionalComponent.orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));

        Optional<Wiring> anyWiringWithId = component.getWirings().stream().filter(w -> w.getId().equals(wiringDto.getId())).findAny();
        log.info("Number of wiring for component: {}", component.getWirings().size());
        log.info("Wiring binding exists: {}", anyWiringWithId.isPresent());

        if (!anyWiringWithId.isPresent()){
            log.info("Adding wiring to component");
            component.getWirings().add(wiring);
            componentRepository.save(component);
        }
        return component;
    }

}
