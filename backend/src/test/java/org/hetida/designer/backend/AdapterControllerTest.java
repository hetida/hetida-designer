package org.hetida.designer.backend;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.hetida.designer.backend.dto.adapter.ModulAdapterDTO;
import org.junit.Before;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

public class AdapterControllerTest extends AbstractTest {

    private static final String ADAPTER_PATH = "/adapters/";

    @Autowired
    private ObjectMapper objectMapper;


    @Before
    public void setup(){
        super.setUp();
        //...
    }

    @Test
    public void testGetAllAdapters() throws Exception{
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        List<ModulAdapterDTO> adapters = objectMapper.readValue(getMvcResultContent, new TypeReference<List<ModulAdapterDTO>>(){});
        assertNotNull(adapters);
        assertEquals(1, adapters.size());
        assertEquals("H4W-HD-Adapter", adapters.get(0).getId());
    }

    @Test
    public void testGetMetadataForNonExistingAdapter() throws Exception{
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "/666/metadata")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(404, status);
    }

    @Test
    public void testGetMetadataForExistingAdapterWithoutImplementation() throws Exception{
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(ADAPTER_PATH + "/1/metadata")
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(500, status);
    }
}
