package org.hetida.designer.backend;


import org.hetida.designer.backend.dto.ComponentDTO;
import org.hetida.designer.backend.dto.IODTO;
import org.hetida.designer.backend.enums.IOType;
import org.hetida.designer.backend.enums.ItemState;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.util.UUID;

import static org.junit.Assert.*;


public class ComponentControllerTest extends AbstractTest {
    private static final String BASE_PATH = "/";


    @Override
    @Before
    public void setUp() {
        super.setUp();
    }

    @Test
    public void createGetModifyAndDeleteComponent() throws Exception {
        final UUID componentId = UUID.randomUUID();
        final UUID componentOutputId = UUID.randomUUID();
        String componentUri = BASE_PATH + "components/" + componentId;
        String listUri = BASE_PATH + "base-items";
        String componentsUri = BASE_PATH + "components";

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


        //Step 2: Check if it appears in our component list
        MvcResult listMvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int listStatus = listMvcResult.getResponse().getStatus();
        assertEquals(200, listStatus);
        String contentList = listMvcResult.getResponse().getContentAsString();
        assertTrue(contentList.contains(componentId.toString()));

        //Step 3: Get component
        MvcResult getMvcResult = mvc.perform(MockMvcRequestBuilders.get(componentUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int getStatus = getMvcResult.getResponse().getStatus();
        assertEquals(200, getStatus);
        String getMvcResultContent = getMvcResult.getResponse().getContentAsString();
        ComponentDTO receivedComponent=super.mapFromJson(getMvcResultContent,ComponentDTO.class);

        //Step 4: Modify component
        receivedComponent.setName("ConstantUpdate");
        String receivedComponentChangedJson = super.mapToJson(receivedComponent);
        MvcResult updateMvcResult = mvc.perform(MockMvcRequestBuilders.put(componentUri).contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(receivedComponentChangedJson)).andReturn();
        int updateStatus = updateMvcResult.getResponse().getStatus();
        assertEquals(201, updateStatus);

        //Step 5: Get again, check changes
        MvcResult getMvcResult2 = mvc.perform(MockMvcRequestBuilders.get(componentUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int getStatus2 = getMvcResult.getResponse().getStatus();
        assertEquals(200, getStatus2);
        String getMvcResult2Content = getMvcResult2.getResponse().getContentAsString();
        ComponentDTO receivedComponent2=super.mapFromJson(getMvcResult2Content,ComponentDTO.class);
        assertEquals("ConstantUpdate", receivedComponent2.getName());

        //Step 6: Delete component
        MvcResult deleteMvcResult = mvc.perform(MockMvcRequestBuilders.delete(componentUri)).andReturn();
        int deleteStatus = deleteMvcResult.getResponse().getStatus();
        assertEquals(204, deleteStatus);

        //Step 7: check if list is empty
        MvcResult list2MvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int list2Status = list2MvcResult.getResponse().getStatus();
        assertEquals(200, list2Status);
        String list2Content = list2MvcResult.getResponse().getContentAsString();
        assertFalse(list2Content.contains(componentId.toString()));

    }





}