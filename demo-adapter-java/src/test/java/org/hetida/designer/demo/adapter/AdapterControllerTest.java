package org.hetida.designer.demo.adapter;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.hetida.designer.demo.adapter.dto.*;
import org.junit.Before;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.time.Instant;
import java.util.List;
import java.util.stream.Collectors;

import static org.junit.Assert.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class AdapterControllerTest extends AbstractTest {

    private static final String ADAPTER_PATH = "/adapter/";

    @Autowired
    private ObjectMapper objectMapper;

    @Before
    public void setUp()  {
        super.setUp();
    }

    @Test
    public void getAdapterInfo() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "info")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        AdapterInfoDTO adapterInfo = objectMapper.readValue(
                getMvcResultContent, new TypeReference<AdapterInfoDTO>() {});
        assertNotNull(adapterInfo);
        assertEquals("DEMO-HD-Adapter", adapterInfo.getId());
        assertEquals("DEMO-HD-Adapter", adapterInfo.getName());
    }

    @Test
    public void getStructure() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders
                .get(ADAPTER_PATH + "structure")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        StructureDTO structureDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<StructureDTO>() {});

        // we expect only the root thing node here
        assertNotNull(structureDTO);
        assertEquals("DEMO-HD-Adapter", structureDTO.getId());
        assertEquals("DEMO-HD-Adapter", structureDTO.getName());
        assertEquals(1, structureDTO.getThingNodes().size());
        assertEquals(0, structureDTO.getSources().size());
        assertEquals(0, structureDTO.getSinks().size());
    }

    @Test
    public void getStructureForPlantA() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders
                .get(ADAPTER_PATH + "structure?parentId=root.plantA")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        StructureDTO structureDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<StructureDTO>() {});

        // structure for plant A, first level only
        assertNotNull(structureDTO);
        assertEquals("DEMO-HD-Adapter", structureDTO.getId());
        assertEquals("DEMO-HD-Adapter", structureDTO.getName());
        assertEquals(2, structureDTO.getThingNodes().size());
        assertEquals(5, structureDTO.getSources().size());
        assertEquals(2, structureDTO.getSinks().size());
    }

    @Test
    public void getSourceMetadataForPlant() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "sources/root.plantA/metadata/")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTOS = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTOS);
        assertEquals(4, metaDataRequestResponseDTOS.size());
        assertTrue(metaDataRequestResponseDTOS.stream().anyMatch(m -> m.getKey().equals("Temperature Unit")));
    }

    @Test
    public void getSourceMetadata() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "sources/root.plantA.millingUnit.influx.temp/metadata/")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTOS = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTOS);
        assertEquals(4, metaDataRequestResponseDTOS.size());
        assertEquals("Sensor Config", metaDataRequestResponseDTOS.get(0).getKey());
        assertEquals("any", metaDataRequestResponseDTOS.get(0).getDataType());
    }

    @Test
    public void getSourceMetadataReturnsEmptyList() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "sources/root.plantA.millingUnit.influx.temp.xxx/metadata/")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTOS = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTOS);
        assertTrue(metaDataRequestResponseDTOS.isEmpty());
    }

    @Test
    public void getSourceMetadataReturnsEmptyObject() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "sources/root.plantA.millingUnit.influx.temp.xxx/metadata/xxx")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        assertTrue(getMvcResultContent.isEmpty());
    }

    @Test
    public void postSourceMetadata() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post(ADAPTER_PATH
                + "/sources/root.plantB.millingUnit.influx.temp/metadata/Sensor Config")
                .contentType(MediaType.APPLICATION_JSON)
                .content(readPostContentFromFile("/post_sources.json"))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON_UTF8))
                .andExpect(jsonPath("$['key']").value("root.plantB.millingUnit.influx.temp|Last Self-Check Okay"))
                .andExpect(jsonPath("$['value']").value(true))
                .andExpect(jsonPath("$['dataType']").value("boolean"))
                .andExpect(jsonPath("$['isSink']").value(false))
                .andReturn();
    }

    @Test
    public void getSinkMetadataForPlant() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "sinks/root.plantA/metadata/")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTO);
        assertEquals("Anomaly State", metaDataRequestResponseDTO.get(0).getKey());
    }

    @Test
    public void getSinkMetadataForKey() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "sinks/root.plantA.millingUnit.influx.anomaly_score/metadata/Overshooting Allowed")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        MetaDataRequestResponseDTO metaDataRequestResponseDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<MetaDataRequestResponseDTO>() {});
        assertNotNull(metaDataRequestResponseDTO);
        assertEquals("Overshooting Allowed", metaDataRequestResponseDTO.getKey());
        assertEquals("boolean", metaDataRequestResponseDTO.getDataType());
    }

    @Test
    public void getSinkMetadataForKeyReturnsEmptyList() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "sinks/root.plantA.millingUnit.influx.anomaly_score_xxx/metadata/")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTO);
        assertTrue(metaDataRequestResponseDTO.isEmpty());
    }

    @Test
    public void getSinkMetadataReturnsEmptyObject() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "sinks/root.plantA.millingUnit.influx.temp.xxx/metadata/xxx")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        assertTrue(getMvcResultContent.isEmpty());
    }

    @Test
    public void postSinkMetadata() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post(ADAPTER_PATH
                + "/sinks/root.plantB.millingUnit.influx.anomaly_score/metadata/Overshooting Allowed")
                .contentType(MediaType.APPLICATION_JSON)
                .content(readPostContentFromFile("/post_sinks.json"))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON_UTF8))
                .andExpect(jsonPath("$['key']").value("root.plantB.millingUnit.influx.anomaly_score|Overshooting Allowed"))
                .andExpect(jsonPath("$['value']").value(true))
                .andExpect(jsonPath("$['isSink']").value(true))
                .andReturn();
    }

    @Test
    public void getThingNodeById() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "thingNodes/root.plantA")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        ThingNodeDTO thingNodeDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<ThingNodeDTO>() {});
        assertNotNull(thingNodeDTO);
        assertEquals("root.plantA", thingNodeDTO.getId());
        assertEquals("Plant A", thingNodeDTO.getName());
    }

    @Test
    public void getThingNodeMetadataForId() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "thingNodes/root.plantA/metadata")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTOS = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTOS);
        assertEquals(4, metaDataRequestResponseDTOS.size());
        assertEquals("Plant Age in Years", metaDataRequestResponseDTOS.get(0).getKey());
        assertFalse(metaDataRequestResponseDTOS.get(0).isSink());
    }

    @Test
    public void getThingNodeMetadataForIdAndKey() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "thingNodes/root.plantA/metadata/Plant Age in Years")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        MetaDataRequestResponseDTO metaDataRequestResponseDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<MetaDataRequestResponseDTO>() {});
        assertNotNull(metaDataRequestResponseDTO);
        assertEquals("Plant Age in Years", metaDataRequestResponseDTO.getKey());
        assertEquals("int", metaDataRequestResponseDTO.getDataType());
        assertFalse(metaDataRequestResponseDTO.isSink());
    }

    @Test
    public void getThingNodeMetadataForIdReturnsEmptyList() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "thingNodes/root.plantAXXX/metadata")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<MetaDataRequestResponseDTO> metaDataRequestResponseDTOS = objectMapper.readValue(
                getMvcResultContent, new TypeReference<List<MetaDataRequestResponseDTO>>() {});
        assertNotNull(metaDataRequestResponseDTOS);
        assertTrue(metaDataRequestResponseDTOS.isEmpty());
    }

    @Test
    public void getThingNodeMetadataReturnsEmptyObject() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "thingNodes/root.plantAXXX/metadata/xxx")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        assertTrue(getMvcResultContent.isEmpty());
    }

    @Test
    public void postThingNodeMetadata() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post(ADAPTER_PATH
                + "/thingNodes/root.plantA/metadata/Plant Age in Years")
                .contentType(MediaType.APPLICATION_JSON)
                .content(readPostContentFromFile("/post_thingNodes.json"))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON_UTF8))
                .andExpect(jsonPath("$['key']").value("root.plantA|Plant Age in Years"))
                .andExpect(jsonPath("$['value']").value(10))
                .andExpect(jsonPath("$['isSink']").value(false))
                .andReturn();
    }

    @Test
    public void getDataframeMasterdata() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "dataframe?id=root.plantA.masterdata")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andExpect(request().asyncStarted())
                .andDo(MvcResult::getAsyncResult)
                .andExpect(status().isOk())
                .andReturn();

        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        DataFrameDTO dataFrameDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<DataFrameDTO>() {});
        assertNotNull(dataFrameDTO);
        assertEquals(2, dataFrameDTO.getDataframes().size());
        assertEquals("plant_construction_date", dataFrameDTO.getDataframes().get("name"));
    }

    @Test
    public void getTimeseries() throws Exception {
        Instant from = Instant.now().minusSeconds(3600);
        Instant to = Instant.now();

        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "timeseries?id=root.plantA.masterdata&from=" + from + "&to=" + to)
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andExpect(request().asyncStarted())
                .andDo(MvcResult::getAsyncResult)
                .andExpect(status().isOk())
                .andReturn();

        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        TimeseriesDTO timeseriesDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<TimeseriesDTO>() {});
        assertNotNull(timeseriesDTO);
        assertEquals("root.plantA.masterdata", timeseriesDTO.getTimeseriesId());
    }

    @Test
    public void postTimeseries() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post(ADAPTER_PATH
                + "/timeseries?timeseriesId=root.plantA.millingUnit.influx")
                .contentType(MediaType.APPLICATION_JSON)
                .content(readPostContentFromFile("/post_timeseries.json"))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON_UTF8))
                .andExpect(jsonPath("$[*]['timestamp']").isArray())
                .andExpect(jsonPath("$[0]['timestamp']").value("2019-09-12T08:00:00.123000000Z"))
                .andExpect(jsonPath("$[0]['value']").value(4.384852))
                .andReturn();
    }

    @Test
    public void getSources() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders
                .get(ADAPTER_PATH + "sources?filter=")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        SourcesDTO sourcesDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<SourcesDTO>() {});
        assertNotNull(sourcesDTO);
        assertEquals(26, sourcesDTO.getResultCount());
    }

    @Test
    public void getSourceById() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders
                .get(ADAPTER_PATH + "sources/root.plantA.millingUnit.influx.temp")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        SourceDTO sourceDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<SourceDTO>() {});
        assertNotNull(sourceDTO);
        assertEquals("root.plantA.millingUnit.influx.temp", sourceDTO.getId());
        assertEquals("timeseries(float)", sourceDTO.getType());
    }

    @Test
    public void getSinks() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders
                .get(ADAPTER_PATH + "sinks?filter=")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        SourcesDTO sourcesDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<SourcesDTO>() {});
        assertNotNull(sourcesDTO);
        assertEquals(12, sourcesDTO.getResultCount());
    }

    @Test
    public void getSinkById() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders
                .get(ADAPTER_PATH + "sinks/root.plantA.picklingUnit.outfeed.anomaly_score")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        SinkDTO sinkDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<SinkDTO>() {});
        assertNotNull(sinkDTO);
        assertEquals("root.plantA.picklingUnit.outfeed.anomaly_score", sinkDTO.getId());
        assertEquals("timeseries(float)", sinkDTO.getType());
    }

    @Test
    public void getDataframeMaintenanceEvents() throws Exception {
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH
                + "dataframe?id=root.plantB.maintenance_events")
                .accept(MediaType.APPLICATION_JSON_VALUE))
                .andExpect(request().asyncStarted())
                .andDo(MvcResult::getAsyncResult)
                .andExpect(status().isOk())
                .andReturn();

        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        DataFrameDTO dataFrameDTO = objectMapper.readValue(
                getMvcResultContent, new TypeReference<DataFrameDTO>() {});
        assertNotNull(dataFrameDTO);
        assertEquals(4, dataFrameDTO.getDataframes().size());
        assertTrue(getMvcResultContent.contains("\"component_id\":\"AB1234\""));
    }

    @Test
    public void postDataframes() throws Exception {
        mvc.perform(MockMvcRequestBuilders.post(ADAPTER_PATH
                + "/dataframe?id=root.plantA.millingUnit.influx")
                .contentType(MediaType.APPLICATION_JSON)
                .content(readPostContentFromFile("/post_dataframes.json"))
                .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON_UTF8))
                .andExpect(jsonPath("$[*]['component_id']").isArray())
                .andExpect(jsonPath("$[0]['component_id']").value("AB1234"))
                .andExpect(jsonPath("$[0]['timestamp']").value("2020-01-15T07:30:45.000000000Z"))
                .andReturn();
    }

    /* Helper */
    private String readPostContentFromFile(String file) {
        try (InputStream inputStream = getClass().getResourceAsStream(file);
             BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            return reader.lines().collect(Collectors.joining(System.lineSeparator()));
        } catch (IOException e) {
            return "";
        }
    }
}