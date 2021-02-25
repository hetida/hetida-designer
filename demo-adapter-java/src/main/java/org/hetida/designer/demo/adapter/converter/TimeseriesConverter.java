package org.hetida.designer.demo.adapter.converter;

import org.hetida.designer.demo.adapter.dto.TimeseriesDTO;
import org.hetida.designer.demo.adapter.dto.client.ClientTimeseriesDTO;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class TimeseriesConverter {

    public List<TimeseriesDTO> convertToTimeseriesDtos(final List<ClientTimeseriesDTO> clientTimeseriesDtos, final String[] requestIds) {

        List<TimeseriesDTO> resultList = new ArrayList<>();
        for (ClientTimeseriesDTO clientTimeseriesDTO : clientTimeseriesDtos) {
            resultList.add(toTimeseriesDTO(clientTimeseriesDTO, requestIds));
        }

        return resultList;
    }

    private TimeseriesDTO toTimeseriesDTO(final ClientTimeseriesDTO clientTimeseriesDTO, final String[] requestIds) {

        TimeseriesDTO timeseriesDTO = new TimeseriesDTO();
        if (requestIds != null) {
            timeseriesDTO.setTimeseriesId(requestIds[0]);
        } else {
            timeseriesDTO.setTimeseriesId(clientTimeseriesDTO.getChannelId());
        }
        timeseriesDTO.setTimestamp(clientTimeseriesDTO.getTimestamp());
        if (clientTimeseriesDTO.getMeasurement() != null) {
            timeseriesDTO.setValue(clientTimeseriesDTO.getMeasurement());
        }

        return timeseriesDTO;
    }
}
