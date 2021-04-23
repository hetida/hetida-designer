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


import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

public class InfoControllerTest extends AbstractTest {

    private static final String INFO_PATH = "/info/";

    @Autowired
    private ObjectMapper objectMapper;


    @Before
    public void setup(){
        super.setUp();
    }

    @Test
    public void testGetInfo() throws Exception{
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.get(INFO_PATH)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);
        String getMvcResultContent = mvcResult.getResponse().getContentAsString();
        assertNotNull(getMvcResultContent);
    }

}
