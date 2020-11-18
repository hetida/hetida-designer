package org.hetida.designer.backend;

import org.hetida.designer.backend.dto.BaseItemDTO;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.enums.ItemType;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;


public class BaseItemControllerTest extends AbstractTest {
    private static final String BASE_PATH = "/";


    @Override
    @Before
    public void setUp() {
        super.setUp();
    }

    @Test
    public void createAndDeleteComponent() throws Exception {
        final UUID componentId = UUID.randomUUID();
        String itemUri = BASE_PATH + "base-items/" + componentId;
        String componentUri = BASE_PATH + "components/" + componentId;
        String listUri = BASE_PATH + "base-items";

        //Step 1: Create component
        BaseItemDTO component = new BaseItemDTO();
        component.setName("Constant");
        component.setCategory("Elemental Algebra");
        component.setDescription("no descripton yet");
        component.setId(componentId);
        component.setGroupId(componentId);
        component.setState(ItemState.DRAFT);
        component.setTag("1.0.0");
        component.setType(ItemType.COMPONENT);


        String inputJson = super.mapToJson(component);

        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.post(listUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJson)).andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(201, status);

        //Step 2: Check if it appears in our component list
        MvcResult listMvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int listStatus = listMvcResult.getResponse().getStatus();
        assertEquals(200, listStatus);
        String listContent = listMvcResult.getResponse().getContentAsString();
        assertTrue(listContent.contains(componentId.toString()));

        //step 3: update tag
        component.setTag("1.0.2");
        String setTagInputJson = super.mapToJson(component);
        MvcResult mvcResultSetTag = mvc.perform(MockMvcRequestBuilders.put(itemUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(setTagInputJson)).andReturn();

        int statusSetTag = mvcResultSetTag.getResponse().getStatus();
        assertEquals(201, statusSetTag);


        //step 4: get component item
        MvcResult getMvcResult = mvc.perform(MockMvcRequestBuilders.get(itemUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int getStatus = getMvcResult.getResponse().getStatus();
        assertEquals(200, getStatus);
        String getMvcResultContent = getMvcResult.getResponse().getContentAsString();
        BaseItemDTO receivedComponent=super.mapFromJson(getMvcResultContent,BaseItemDTO.class);
        assertEquals("Constant", receivedComponent.getName());

        //Step 5: Delete component
        MvcResult deleteMvcResult = mvc.perform(MockMvcRequestBuilders.delete(componentUri)).andReturn();
        int deleteStatus = deleteMvcResult.getResponse().getStatus();
        assertEquals(204, deleteStatus);

        //Step 6: check if list is empty
        MvcResult list2MvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int list2Status = list2MvcResult.getResponse().getStatus();
        assertEquals(200, list2Status);
        String list2Content = list2MvcResult.getResponse().getContentAsString();
        assertTrue(!list2Content.contains(componentId.toString()));

    }

    @Test
    public void createAndDeleteWorkflow() throws Exception {
        final UUID workflowId = UUID.randomUUID();
        String itemUri = BASE_PATH + "base-items/" + workflowId;
        String workflowUri = BASE_PATH + "workflows/" + workflowId;
        String listUri = BASE_PATH + "base-items";

        //Step 1: Create workflow
        String uri = BASE_PATH + "base-items";
        BaseItemDTO workflow = new BaseItemDTO();
        workflow.setName("Testworkflow");
        workflow.setCategory("Elemental Algebra");
        workflow.setDescription("no description yet");
        workflow.setId(workflowId);
        workflow.setGroupId(workflowId);
        workflow.setState(ItemState.DRAFT);
        workflow.setTag("1.0.0");
        workflow.setType(ItemType.WORKFLOW);


        String inputJson = super.mapToJson(workflow);
        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.post(uri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJson)).andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(201, status);

        //Step 2: Check if it appears in our component list
        MvcResult listMvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int listStatus = listMvcResult.getResponse().getStatus();
        assertEquals(200, listStatus);
        String listContent = listMvcResult.getResponse().getContentAsString();
        assertTrue(listContent.contains(workflowId.toString()));


        //step 3: update tag
        workflow.setTag("1.0.1");
        String setTagInputJson = super.mapToJson(workflow);
        MvcResult mvcResultSetTag = mvc.perform(MockMvcRequestBuilders.put(itemUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(setTagInputJson)).andReturn();

        int statusSetTag = mvcResultSetTag.getResponse().getStatus();
        assertEquals(201, statusSetTag);

        //step 4: get workflow item
        MvcResult getMvcResult = mvc.perform(MockMvcRequestBuilders.get(itemUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int getStatus = getMvcResult.getResponse().getStatus();
        assertEquals(200, getStatus);
        String getMvcResultContent = getMvcResult.getResponse().getContentAsString();
        BaseItemDTO receivedWorkflow=super.mapFromJson(getMvcResultContent,BaseItemDTO.class);
        assertEquals("Testworkflow", receivedWorkflow.getName());

        //Step 5: Delete component
        MvcResult deleteMvcResult = mvc.perform(MockMvcRequestBuilders.delete(workflowUri)).andReturn();
        int deleteStatus = deleteMvcResult.getResponse().getStatus();
        assertEquals(204, deleteStatus);

        //Step 6: check if list is empty
        MvcResult list2MvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int list2Status = list2MvcResult.getResponse().getStatus();
        assertEquals(200, list2Status);
        String list2Content = list2MvcResult.getResponse().getContentAsString();
        assertTrue(!list2Content.contains(workflowId.toString()));

    }


}