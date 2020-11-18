package org.hetida.designer.backend.converter;

import lombok.extern.log4j.Log4j2;
import org.hetida.designer.backend.dto.PointDTO;
import org.hetida.designer.backend.model.Point;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Component
@Log4j2
public class PointConverter {

    public List<PointDTO> convertToPointDtos(final List<Point> entities) {
        return entities == null ? null : entities.stream()
                .map(this::convertToPointDto)
                .collect(Collectors.toList());
    }

    public List<Point> convertToPointEntities(final List<PointDTO> dtos) {

        List<Point> points = new ArrayList<>();
        if (dtos != null) {
            int currentSequenceNr = 0;
            for (PointDTO point : dtos) {
                points.add(this.convertToPointEntity(point, currentSequenceNr));
                currentSequenceNr++;
            }
        }
        return points;
    }

    private PointDTO convertToPointDto(Point entity) {
        PointDTO pointDTO = new PointDTO();
        pointDTO.setId(entity.getId());
        pointDTO.setPosX(entity.getPosX());
        pointDTO.setPosY(entity.getPosY());
        return pointDTO;
    }

    private Point convertToPointEntity(PointDTO dto, int sequenceNr) {
        Point point = new Point();
        point.setId(dto.getId());
        point.setPosX(dto.getPosX());
        point.setPosY(dto.getPosY());
        point.setSequenceNr(sequenceNr);
        return point;
    }
}
