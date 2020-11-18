package org.hetida.designer.backend;

import org.hetida.designer.backend.dto.DocumentationDTO;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.util.UUID;

import static org.junit.Assert.*;


public class DocumentationControllerTest extends AbstractTest {
    private static final String BASE_PATH = "/";


    @Override
    @Before
    public void setUp() {
        super.setUp();
    }

    @Test
    public void createAndDeleteDocumentation() throws Exception {
        final UUID documentationId = UUID.randomUUID();

        String documentationUri = BASE_PATH + "documentations/" + documentationId;

        //Step 1: Create documentation
        DocumentationDTO documentation = new DocumentationDTO();
        documentation.setId(documentationId);
        documentation.setDocument("test documentation");


        String inputJson = super.mapToJson(documentation);

        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.put(documentationUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJson)).andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(200, status);


        //Step 2: Check if get works
        MvcResult listMvcResult = mvc.perform(MockMvcRequestBuilders.get(documentationUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int listStatus = listMvcResult.getResponse().getStatus();
        assertEquals(200, listStatus);
        String content = listMvcResult.getResponse().getContentAsString();
        assertTrue(content.contains(documentation.getDocument()));

        //Step 3: Delete documentation
        MvcResult deleteMvcResult = mvc.perform(MockMvcRequestBuilders.delete(documentationUri)).andReturn();
        int deleteStatus = deleteMvcResult.getResponse().getStatus();
        assertEquals(204, deleteStatus);

        //Step 4: check if get returns empty documentation
        MvcResult emptyResult = mvc.perform(MockMvcRequestBuilders.get(documentationUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int emptyResultStatus = emptyResult.getResponse().getStatus();
        assertEquals(200, emptyResultStatus);
        String emptyResultContent = emptyResult.getResponse().getContentAsString();
        assertFalse(emptyResultContent.contains(documentation.getDocument()));

    }


}