package org.hetida.designer.backend;

import org.hetida.designer.backend.dto.*;
import org.hetida.designer.backend.enums.IOType;
import org.hetida.designer.backend.enums.ItemState;
import org.hetida.designer.backend.enums.ItemType;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;


public class WorkflowControllerTest extends AbstractTest {
    private static final String BASE_PATH = "/";


    @Override
    @Before
    public void setUp() {
        super.setUp();


    }


    @Test
    public void createAndDeleteWorkflow() throws Exception {
        // prepare components
        //create ids for further reference

        final UUID component1Id = UUID.randomUUID();
        final UUID component1Output = UUID.randomUUID();

        final UUID component2Id = UUID.randomUUID();
        final UUID component2Input = UUID.randomUUID();

        final UUID workflowId = UUID.randomUUID();
        final UUID operator1Id = UUID.randomUUID();
        final UUID operator2Id = UUID.randomUUID();

        final UUID linkId = UUID.randomUUID();

        String workflowUri = BASE_PATH + "workflows/" + workflowId;

        //create test components to use as operator
        //Step 1: Create component1
        String createComponentUri = BASE_PATH + "components";
        ComponentDTO component1 = new ComponentDTO();
        component1.setName("Constant");
        component1.setCategory("Elemental Algebra");
        component1.setCode("from hetdesrun.component.registration import register\\nfrom hetdesrun.datatypes import DataType\\n\\nimport pandas as pd\\nimport numpy as np\\n# ***** DO NOT EDIT LINES BELOW *****\\n# These lines may be overwritten if input/output changes.\\n@register(\\n    inputs={}, outputs={\\\"c\\\": DataType.Float}\\n)\\ndef main():\\n    # ***** DO NOT EDIT LINES ABOVE *****\\n    return {\\\"c\\\": 5.0}\\n\",\n");
        component1.setDescription("no description yet");
        component1.setId(component1Id);
        component1.setGroupId(component1Id);
        component1.setState(ItemState.DRAFT);
        component1.setTag("1.0.0");

        IODTO outputComponent1 = new IODTO();
        outputComponent1.setName("c");
        outputComponent1.setType(IOType.FLOAT);
        outputComponent1.setId(component1Output);
        component1.getOutputs().add(outputComponent1);

        String inputJsonComponent1 = super.mapToJson(component1);

        MvcResult mvcResultComponent1 = mvc.perform(MockMvcRequestBuilders.post(createComponentUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJsonComponent1)).andReturn();

        int statusComponent1 = mvcResultComponent1.getResponse().getStatus();
        assertEquals(201, statusComponent1);

        //Step 2: Create component1
        ComponentDTO component2 = new ComponentDTO();
        component2.setName("Constant");
        component2.setCategory("Elemental Algebra");
        component2.setCode("from hetdesrun.component.registration import register\\nfrom hetdesrun.datatypes import DataType\\n\\nimport pandas as pd\\nimport numpy as np\\n# ***** DO NOT EDIT LINES BELOW *****\\n# These lines may be overwritten if input/output changes.\\n@register(\\n    inputs={}, outputs={\\\"c\\\": DataType.Float}\\n)\\ndef main():\\n    # ***** DO NOT EDIT LINES ABOVE *****\\n    return {\\\"c\\\": 5.0}\\n\",\n");
        component2.setDescription("no description yet");
        component2.setId(component2Id);
        component2.setGroupId(component2Id);
        component2.setState(ItemState.DRAFT);
        component2.setTag("1.0.0");

        IODTO inputComponent2 = new IODTO();
        inputComponent2.setName("c");
        inputComponent2.setType(IOType.FLOAT);
        inputComponent2.setId(component2Input);
        component2.getInputs().add(inputComponent2);

        String inputJsonComponent2 = super.mapToJson(component2);

        MvcResult mvcResultComponent2 = mvc.perform(MockMvcRequestBuilders.post(createComponentUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJsonComponent2)).andReturn();

        int statusComponent2 = mvcResultComponent2.getResponse().getStatus();
        assertEquals(201, statusComponent2);


        //Step 3: Create workflow
        String uri = BASE_PATH + "workflows";
        WorkflowDTO workflow = new WorkflowDTO();
        workflow.setName("Testworkflow");
        workflow.setCategory("Tests");
        workflow.setDescription("no description yet");
        workflow.setId(workflowId);
        workflow.setGroupId(workflowId);
        workflow.setState(ItemState.DRAFT);
        workflow.setTag("1.0.0");


        String inputJson = super.mapToJson(workflow);

        MvcResult mvcResult = mvc.perform(MockMvcRequestBuilders.post(uri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputJson)).andReturn();

        int status = mvcResult.getResponse().getStatus();
        assertEquals(201, status);
        String content = mvcResult.getResponse().getContentAsString();
        assertNotNull(content);

        //Step 4: Check if it appears in our component list
        String listUri = BASE_PATH + "base-items";
        MvcResult listMvcResult = mvc.perform(MockMvcRequestBuilders.get(listUri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int listStatus = listMvcResult.getResponse().getStatus();
        assertEquals(200, listStatus);
        String listContent = listMvcResult.getResponse().getContentAsString();
        assertTrue(listContent.contains(component1Id.toString()));
        assertTrue(listContent.contains(component2Id.toString()));
        assertTrue(listContent.contains(workflowId.toString()));

        //step 6: add component1 as operator
        WorkflowOperatorDTO operator1 = new WorkflowOperatorDTO();
        operator1.setId(operator1Id);
        operator1.setPosY(50);
        operator1.setPosX(50);
        operator1.setType(ItemType.COMPONENT);
        operator1.setItemId(component1Id);
        workflow.getOperators().add(operator1);
        String inputOperator1Json = super.mapToJson(workflow);

        MvcResult mvcResultOperator1 = mvc.perform(MockMvcRequestBuilders.put(workflowUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputOperator1Json)).andReturn();

        int statusOperator1 = mvcResultOperator1.getResponse().getStatus();
        assertEquals(201, statusOperator1);

        //step 7: verify component1 as operator
        MvcResult mvcResultOperator1Get = mvc.perform(MockMvcRequestBuilders.get(workflowUri).accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int mvcResultOperator1GetStatus = mvcResultOperator1Get.getResponse().getStatus();
        assertEquals(200, mvcResultOperator1GetStatus);
        String operator1GetStatusContent = mvcResultOperator1Get.getResponse().getContentAsString();
        assertTrue(operator1GetStatusContent.contains(operator1Id.toString()));

        //step 8: add component2 as operator
        WorkflowOperatorDTO operator2 = new WorkflowOperatorDTO();
        operator2.setId(operator2Id);
        operator2.setPosY(250);
        operator2.setPosX(250);
        operator2.setType(ItemType.COMPONENT);
        operator2.setItemId(component2Id);
        workflow.getOperators().add(operator2);
        String inputOperator2Json = super.mapToJson(workflow);

        MvcResult mvcResultOperator2 = mvc.perform(MockMvcRequestBuilders.put(workflowUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(inputOperator2Json)).andReturn();

        int statusOperator2 = mvcResultOperator2.getResponse().getStatus();
        assertEquals(201, statusOperator2);

        //step 9: verify component2 as operator
        MvcResult mvcResultOperator2Get = mvc.perform(MockMvcRequestBuilders.get(workflowUri).accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        int mvcResultOperator2GetStatus = mvcResultOperator2Get.getResponse().getStatus();
        assertEquals(200, mvcResultOperator2GetStatus);
        String operator2GetStatusContent = mvcResultOperator2Get.getResponse().getContentAsString();
        System.out.println(operator2GetStatusContent);
        assertTrue(operator2GetStatusContent.contains(operator2Id.toString()));

        //step 10: add link between component1 output and component2 input
        WorkflowLinkDTO link = new WorkflowLinkDTO();
        link.setId(linkId);
        link.setFromOperator(operator1Id);
        link.setFromConnector(component1Output);
        link.setToOperator(operator2Id);
        link.setToConnector(component2Input);
        workflow.getLinks().add(link);
        String linkJson = super.mapToJson(workflow);

        MvcResult mvcResultLink = mvc.perform(MockMvcRequestBuilders.put(workflowUri)
                .contentType(MediaType.APPLICATION_JSON_VALUE)
                .content(linkJson)).andReturn();

        int statusLink = mvcResultLink.getResponse().getStatus();
        assertEquals(201, statusLink);

        //step 11: verify link
        MvcResult mvcResultLinkGet = mvc.perform(MockMvcRequestBuilders.get(workflowUri).accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();
        assertEquals(200, mvcResultLinkGet.getResponse().getStatus());
        String linkGetStatusContent = mvcResultLinkGet.getResponse().getContentAsString();
        assertTrue(linkGetStatusContent.contains(linkId.toString()));

        /* workflow outputs & input
         WorkflowNodeIODTO output1=new WorkflowNodeIODTO();
         output1.setName("c");
         output1.setType(IOType.FLOAT);
         output1.setId(UUID.fromString("627486b6-7e05-4dcb-89bd-d176b508fc9d"));
         workflow.getOutputs().add(output1);
         */

        //Step 12: Delete workflow
        MvcResult deleteMvcResult = mvc.perform(MockMvcRequestBuilders.delete(workflowUri)).andReturn();
        int deleteStatus = deleteMvcResult.getResponse().getStatus();
        assertEquals(204, deleteStatus);

        //Step 13: check if workflow was deleted
        String list2Uri = BASE_PATH + "base-items";
        MvcResult list2MvcResult = mvc.perform(MockMvcRequestBuilders.get(list2Uri)
                .accept(MediaType.APPLICATION_JSON_VALUE)).andReturn();

        int list2Status = list2MvcResult.getResponse().getStatus();
        assertEquals(200, list2Status);
        String list2Content = list2MvcResult.getResponse().getContentAsString();
        assertTrue(!list2Content.contains(workflowId.toString()));

        //step 14: cleanup components
        String deleteComponentUri = BASE_PATH + "components/";
        MvcResult deleteMvcResultComponent1 = mvc.perform(MockMvcRequestBuilders.delete(deleteComponentUri + component1Id)).andReturn();
        int deleteStatusComponent1 = deleteMvcResultComponent1.getResponse().getStatus();
        assertEquals(204, deleteStatusComponent1);

        MvcResult deleteMvcResultComponent2 = mvc.perform(MockMvcRequestBuilders.delete(deleteComponentUri + component2Id)).andReturn();
        int deleteStatusComponent2 = deleteMvcResultComponent2.getResponse().getStatus();
        assertEquals(204, deleteStatusComponent2);

    }


}