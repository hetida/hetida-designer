package org.hetida.designer.demo.adapter.client;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.MappingIterator;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;
import org.hetida.designer.demo.adapter.dto.DataFrameDTO;
import org.hetida.designer.demo.adapter.dto.TimeSeriesCriteriaDto;
import org.hetida.designer.demo.adapter.dto.client.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpStatusCodeException;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.stream.Collectors;

@Component
@Log4j2
public class AdapterClient {

    private final ObjectMapper objectMapper;

    public AdapterClient(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    public ClientStructureDTO getStructure() throws HttpStatusCodeException {
        try {
            return createClientStructureMock();
        } catch (Exception e) {
            log.error(e);
            return null;
        }
    }

    public List<ClientSinkDTO> getSinks() {
        ClientStructureDTO clientStructureDTO = new ClientStructureDTO();
        try {
            readSinks(clientStructureDTO);
        } catch (IOException e) {
            log.error(e);
            return null;
        }
        return clientStructureDTO.getSinks().getSinks();
    }

    public List<ClientSourceDTO> getSources() {
        ClientStructureDTO clientStructureDTO = new ClientStructureDTO();
        try {
            readSources(clientStructureDTO);
        } catch (IOException e) {
            log.error(e);
            return null;
        }
        return clientStructureDTO.getSources().getSources();
    }

    public ClientMetaDataDTO getMetaData() {
        try {
            return createClientMetaDataMock();
        } catch (Exception e) {
            log.error(e);
            return null;
        }
    }

    public List<ClientTimeseriesDTO> getTimeseries(final String callType, final TimeSeriesCriteriaDto timeSeriesCriteriaDto) throws HttpStatusCodeException {

        try {
            return getListFromLineDelimitedJson(createClientTimeseriesMock(), ClientTimeseriesDTO.class);

        } catch (Exception e) {
            log.error(e);
            return null;
        }
    }

    public ArrayList<LinkedHashMap> getDataframe(final String id, TimeSeriesCriteriaDto timeSeriesCriteriaDto) throws HttpStatusCodeException {
        try {
            if (id != null && id.endsWith("masterdata")) {
                ArrayList<LinkedHashMap> masterdata = (ArrayList<LinkedHashMap>) createClientDataframeMock(id).getDataframes().get("masterdata");
                return masterdata;
            } else if (id != null && id.endsWith("maintenance_events")) {
                ArrayList<LinkedHashMap> maintenance_events = (ArrayList<LinkedHashMap>) createClientMaintenanceEvents(id).getDataframes().get("maintenanceEvents");
                return maintenance_events;
            }
            return new ArrayList<>();
        } catch (Exception e) {
            log.error(e);
            return null;
        }
    }

    private DataFrameDTO createClientDataframeMock(String id) throws IOException {
        if (id != null && id.equals("root.plantA.masterdata")) {
            return readMasterdataPlantA();
        } else if (id != null && id.equals("root.plantB.masterdata")) {
            return readMasterdataPlantB();
        }
        return null;
    }

    private DataFrameDTO createClientMaintenanceEvents(String id) throws IOException {
        if (id != null && id.equals("root.plantA.maintenance_events")) {
            return readMaintenanceEventsPlantA();
        } else if (id != null && id.equals("root.plantB.maintenance_events")) {
            return readMaintenanceEventsPlantB();
        }
        return null;
    }

    private <T> List<T> getListFromLineDelimitedJson(final String json, final Class clazz) throws IOException {

        final List<T> listOfObjects = new ArrayList<>();
        final MappingIterator<T> iterator = objectMapper.readerFor(clazz).readValues(json);
        while (iterator.hasNext()) {
            final T value = iterator.nextValue();
            listOfObjects.add(value);
        }
        return listOfObjects;
    }

    private ClientMetaDataDTO createClientMetaDataMock() throws Exception {
        return readMetadata();
    }

    private ClientStructureDTO createClientStructureMock() throws Exception {
        ClientStructureDTO clientStructureDTO = new ClientStructureDTO();
        readThingNodes(clientStructureDTO);
        readSources(clientStructureDTO);
        readSinks(clientStructureDTO);
        return clientStructureDTO;
    }

    private String createClientTimeseriesMock() throws Exception {

        String contents = "";
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/timeseries.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
        }

        return contents;
    }

    private DataFrameDTO readMasterdataPlantA() throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/masterdata_plant_a.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            return objectMapper.readValue(contents, new TypeReference<DataFrameDTO>(){});
        }
    }

    private DataFrameDTO readMasterdataPlantB() throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/masterdata_plant_b.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            return objectMapper.readValue(contents, new TypeReference<DataFrameDTO>(){});
        }
    }

    private DataFrameDTO readMaintenanceEventsPlantA() throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/maintenance_events_plant_a.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            return objectMapper.readValue(contents, new TypeReference<DataFrameDTO>(){});
        }
    }

    private DataFrameDTO readMaintenanceEventsPlantB() throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/maintenance_events_plant_b.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            return objectMapper.readValue(contents, new TypeReference<DataFrameDTO>(){});
        }
    }

    private void readThingNodes(ClientStructureDTO clientStructureDTO) throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/thing_nodes.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            ClientThingNodesDTO thingNodes = objectMapper.readValue(contents, new TypeReference<ClientThingNodesDTO>(){});
            clientStructureDTO.setThingNodes(thingNodes);
        }
    }

    private void readSources(ClientStructureDTO clientStructureDTO) throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/sources.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            ClientSourcesDTO sources = objectMapper.readValue(contents, new TypeReference<ClientSourcesDTO>(){});
            clientStructureDTO.setSources(sources);
        }
    }

    private void readSinks(ClientStructureDTO clientStructureDTO) throws IOException {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/sinks.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            ClientSinksDTO sinks = objectMapper.readValue(contents, new TypeReference<ClientSinksDTO>(){});
            clientStructureDTO.setSinks(sinks);
        }
    }

    private ClientMetaDataDTO readMetadata() throws Exception {
        try (InputStream inputStream = getClass().getResourceAsStream("/demo-data/metadata.json");
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            String contents = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            ClientMetaDataDTO clientMetaDataDTO = objectMapper.readValue(contents, new TypeReference<ClientMetaDataDTO>(){});
            return clientMetaDataDTO;
        }
    }
}
