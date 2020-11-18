package org.hetida.designer.backend;

import org.hetida.designer.backend.dto.ComponentDTO;
import org.hetida.designer.backend.dto.IODTO;
import org.hetida.designer.backend.dto.WiringDTO;
import org.hetida.designer.backend.enums.IOType;
import org.hetida.designer.backend.enums.ItemState;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.util.ArrayList;
import java.util.UUID;

import static org.junit.Assert.*;

public class ComponentExecutionControllerTest extends AbstractTest{
    private static final String BASE_PATH = "/";


    @Override
    @Before
    public void setUp() {
        super.setUp();
    }

    @Test
    public void createAndExecuteComponent() throws Exception {
        final UUID componentId = UUID.randomUUID();
        final UUID componentOutputId = UUID.randomUUID();
        String componentsUri = BASE_PATH + "components/";
        String componentUri = componentsUri + componentId;
        String executeUri = componentUri + "/execute/";

        //Step 1: Create component
        ComponentDTO component = new ComponentDTO();
        component.setName("Constant");
        component.setCategory("Elemental Algebra");
        component.setCode("from hetdesrun.component.registration import register\\nfrom hetdesrun.datatypes import DataType\\n\\nimport pandas as pd\\nimport numpy as np\\n# ***** DO NOT EDIT LINES BELOW *****\\n# These lines may be overwritten if input/output changes.\\n@register(\\n    inputs={}, outputs={\\\"c\\\": DataType.Float}\\n)\\ndef main():\\n    # ***** DO NOT EDIT LINES ABOVE *****\\n    return {\\\"c\\\": 5.0}\\n\",\n");
        component.setDescription("no description yet");
        component.setId(componentId);
        component.setGroupId(componentId);
        component.setState(ItemState.DRAFT);
        component.setTag("1.0.0");

        IODTO output1 = new IODTO();
        output1.setName("c");
        output1.setType(IOType.FLOAT);
        output1.setId(componentOutputId);
        component.getOutputs().add(output1);

        String inputJson = super.mapToJson(component);

        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.post(componentsUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJson)).andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(201, status);

        //Step 2: Get component
        MvcResult getMvcResult = mvc.perform(MockMvcRequestBuilders.get(componentUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int getStatus = getMvcResult.getResponse().getStatus();
        assertEquals(200, getStatus);
        String getMvcResultContent = getMvcResult.getResponse().getContentAsString();
        ComponentDTO receivedComponent=super.mapFromJson(getMvcResultContent,ComponentDTO.class);
        assertNotNull(receivedComponent);

        //Step 3: Execute component
        WiringDTO wiringDto = new WiringDTO();
        wiringDto.setInputWirings(new ArrayList<>());
        wiringDto.setOutputWirings(new ArrayList<>());

        String executionJSON = super.mapToJson(wiringDto);
        MvcResult executeMvcResult = mvc.perform(MockMvcRequestBuilders.post(executeUri).contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(executionJSON)).andReturn();
        int executeStatus = executeMvcResult.getResponse().getStatus();
        assertEquals(200, executeStatus);

         //Step 4: Delete component
        MvcResult deleteMvcResult = mvc.perform(MockMvcRequestBuilders.delete(componentUri)).andReturn();
        int deleteStatus = deleteMvcResult.getResponse().getStatus();
        assertEquals(204, deleteStatus);
    }

}
