package org.hetida.designer.backend.service.impl;

import java.util.List;

import org.hetida.designer.backend.model.Wiring;
import org.hetida.designer.backend.repository.WiringRepository;
import org.hetida.designer.backend.service.WiringService;
import org.springframework.stereotype.Service;


@Service
public class WiringServiceImpl implements WiringService {

    private final WiringRepository wiringRepository;

    public WiringServiceImpl(WiringRepository wiringRepository) {
        this.wiringRepository = wiringRepository;
    }

    @Override
    public Wiring create(Wiring wiring) {
        return this.wiringRepository.save(wiring);
    }

    @Override
    public List<Wiring> getAll() {
        return this.wiringRepository.findAll();
    }

    @Override
    public Wiring update(Wiring wiring) {
        return this.wiringRepository.save(wiring);
    }

}
