import { Injectable } from '@angular/core';
import {
  FlowchartComponent,
  FlowchartComponentIO,
  FlowchartComponentLink,
  FlowchartConfiguration,
  IOType
} from 'hetida-flowchart';
import { RevisionState } from 'src/app/enums/revision-state';
import { Point } from 'src/app/model/point';
import { v4 as UUID } from 'uuid';
import {
  Transformation,
  WorkflowTransformation
} from '../../model/new-api/transformation';

@Injectable({
  providedIn: 'root'
})
export class FlowchartConverterService {
  // TODO rename to convertTransformationToFlowchartForPreview?
  /**
   * converts the given base item to a flowchart configuration
   * @param transformation given base item
   */
  public convertComponentToFlowchart(
    transformation: Transformation
  ): FlowchartConfiguration {
    // TODO this method is also used for workflows?
    // should remove constants if transformation is workflow
    const cleanedComponent = { ...transformation };
    const operator = this.convertBaseItemToFlowchartOperator(
      cleanedComponent,
      0,
      0
    );
    return {
      id: '',
      components: [operator],
      io: [],
      links: []
    };
  }

  /**
   * converts the given workflow to a flowchart configuration
   * @param workflow given workflow
   */
  public convertWorkflowToFlowchart(
    workflow: WorkflowTransformation
  ): FlowchartConfiguration {
    // don't show workflow io without a name
    const workflowClean = { ...workflow };
    workflowClean.content.inputs = workflowClean.content.inputs.filter(
      io => io.name !== '' && io.name !== null && io.name !== undefined
    );
    workflowClean.content.outputs = workflowClean.content.outputs.filter(
      io => io.name !== '' && io.name !== null && io.name !== undefined
    );

    const flowchart = {
      id: workflow.id,
      components: this.convertWorkflowOperatorsToFlowchartComponents(
        workflowClean
      ),
      io: this.convertWorkflowIOToFlowchartIO(workflowClean),
      links: this.convertWorkflowLinksToFlowchartLinks(workflowClean)
    } as FlowchartConfiguration;
    // TODO no need anymore
    // this.convertWorkflowConstants(workflowClean, flowchart);

    return flowchart;
  }

  // TODO no need anymore
  // private convertWorkflowConstants(
  //   workflow: WorkflowBaseItem,
  //   flowchart: FlowchartConfiguration
  // ): void {
  //   const convertIoItem = (io: IOItem, isInput: boolean) => {
  //     if (io.constant === undefined || io.constant === false) {
  //       return;
  //     }
  //     if (io.operator === undefined || io.connector === undefined) {
  //       return;
  //     }
  //     const component = flowchart.components.find(
  //       flowchartComponent => flowchartComponent.uuid === io.operator
  //     );
  //     if (component === undefined) {
  //       return;
  //     }
  //     const connector = (isInput ? component.inputs : component.outputs).find(
  //       input => input.uuid === `${io.operator}_${io.connector}`
  //     );
  //     if (connector === undefined) {
  //       return;
  //     }
  //     connector.constant = true;
  //     connector.value = io.constantValue.value;

  //     flowchart.links = flowchart.links.filter(
  //       link =>
  //         (isInput ? link.to : link.from) !==
  //         `link-${io.operator}_${io.connector}`
  //     );
  //   };

  //   for (const input of workflow.inputs) {
  //     convertIoItem(input, true);
  //   }
  //   for (const output of workflow.outputs) {
  //     convertIoItem(output, false);
  //   }
  // }

  /**
   * converts all operators of the given workflow to flowchart components
   * @param workflow given workflow
   */
  private convertWorkflowOperatorsToFlowchartComponents(
    workflow: WorkflowTransformation
  ): FlowchartComponent[] {
    const components: Array<FlowchartComponent> = [];

    for (const operator of workflow.content.operators) {
      const transformation: Transformation = {
        id: operator.id,
        revision_group_id: operator.revision_group_id,
        name: operator.name,
        category: '',
        version_tag: operator.version_tag,
        state: operator.state,
        type: operator.type,
        content: null,
        io_interface: {
          inputs: operator.inputs,
          outputs: operator.outputs
        },
        test_wiring: {
          input_wirings: [],
          output_wirings: []
        }
      };

      components.push(
        this.convertBaseItemToFlowchartOperator(
          transformation,
          operator.position.x,
          operator.position.y
        )
      );
    }

    return components;
  }

  // noinspection JSMethodCanBeStatic
  /**
   * converts all IOs of the given workflow to flowchart IOs
   * @param workflow given workflow
   */
  private convertWorkflowIOToFlowchartIO(
    workflow: WorkflowTransformation
  ): FlowchartComponentIO[] {
    // IO is reversed for a workflow, e.g. an output of a workflow takes a value in and transfers it to the world outside the workflow!
    const workflowIO: Array<FlowchartComponentIO> = [];
    for (const io of workflow.content.inputs) {
      // TODO No constants
      // we skip constants as they are handled later on
      // if (io.constant !== undefined && io.constant === true) {
      //   continue;
      // }
      workflowIO.push({
        uuid: `${workflow.id}_${io.id}`,
        data_type: io.data_type as IOType,
        name: io.name === undefined ? '' : io.name,
        input: false,
        pos_x: io.position.x,
        pos_y: io.position.y,
        constant: false,
        value: ''
      });
    }

    for (const io of workflow.content.outputs) {
      // TODO No constants
      // we skip constants as they are handled later on
      // if (io.constant !== undefined && io.constant === true) {
      //   continue;
      // }
      workflowIO.push({
        uuid: `${workflow.id}_${io.id}`,
        data_type: io.data_type as IOType,
        name: io.name === undefined ? '' : io.name,
        input: true,
        pos_x: io.position.x,
        pos_y: io.position.y,
        constant: false,
        value: ''
      });
    }
    return workflowIO;
  }

  // noinspection JSMethodCanBeStatic
  /**
   * converts all links of the given workflow to flowchart links
   * @param workflow given workflow
   */
  private convertWorkflowLinksToFlowchartLinks(
    workflow: WorkflowTransformation
  ): FlowchartComponentLink[] {
    const links: Array<FlowchartComponentLink> = [];

    for (const link of workflow.content.links) {
      // filter constant links
      if (
        workflow.content.constants.find(constant => constant.id === link.id)
      ) {
        continue;
      }

      const linkPath = link.path.map(position => [position.x, position.y]);
      // TODO Check for id
      // const linkIds = link.path.map(point => point.id);
      const linkIds = link.path.map(() => UUID().toString());

      let linkStartOperator = '';
      let linkEndOperator = '';
      // if no operator id is given use the transformation id instead
      if (link.start.operator !== undefined) {
        linkStartOperator = link.start.operator;
      } else {
        linkStartOperator = workflow.id;
      }

      if (link.end.operator !== undefined) {
        linkEndOperator = link.end.operator;
      } else {
        linkEndOperator = workflow.id;
      }

      links.push({
        uuid: link.id,
        from: `link-${linkStartOperator}_${link.start.connector.id}`,
        to: `link-${linkEndOperator}_${link.end.connector.id}`,
        path: linkPath.length === 0 ? null : linkPath,
        path_ids: linkIds.length === 0 ? null : linkIds
      });
    }
    return links;
  }

  /**
   * converts the svg path data and the id's of the points to a Point array
   * @param link svg link element
   */
  public convertLinkPathToPoints(link: Element): Point[] {
    const linkPath = link.getAttribute('d');
    const linkIds = link.getAttribute('custom-path');
    if (linkPath === null || linkIds === null) {
      return [];
    }
    const values = linkPath.split(' L '); // Format is 'M(x) (y) {L (x) (y)}*'
    values[0] = values[0].substr(1); // Format is 'M(x) (y) {L (x) (y)}*', we remove the M
    const coordinates = values.map(pair =>
      pair
        .trim()
        .split(' ')
        .map(str => Number(str))
    );
    const newIds = linkIds
      .split(',')
      .map(id => (id === 'x' ? UUID().toString() : id));
    link.setAttribute('custom-path', newIds.join(','));
    return coordinates.map(
      (coords, index) =>
        ({
          posX: coords[0],
          posY: coords[1],
          id: newIds[index]
        } as Point)
    );
  }

  /**
   * extracts the operator and connector id from the given link element
   * @param link given link element
   * @param from if the start (true) or the end (false) operator and connectors should be extracted
   */
  public getLinkOperatorAndConnector(
    link: Element,
    from: boolean
  ): { operatorId: string; connectorId: string } {
    const ids = link
      .getAttribute(from ? 'link-start' : 'link-end')
      .replace('link-', '')
      .split('_');
    if (ids.length !== 2) {
      throw new Error('Internal Error: Link has insufficient data!');
    }
    return {
      operatorId: ids[0],
      connectorId: ids[1]
    };
  }

  // noinspection JSMethodCanBeStatic
  /**
   * converts a BaseItem to a flowchart operator, if no position is given, it will create a new operator
   * @param transformation BaseItem describing the Operator
   * @param posX x coordinate of the operator
   * @param posY y coordinate of the operator
   */
  private convertBaseItemToFlowchartOperator(
    transformation: Transformation,
    posX: number,
    posY: number
  ): FlowchartComponent {
    let uuid: string;
    if (posX === null && posY === null) {
      uuid = UUID().toString();
    } else {
      uuid = transformation.id;
    }
    const component: FlowchartComponent = {
      uuid,
      name: transformation.name,
      revision: transformation.version_tag,
      inputs: [],
      outputs: [],
      pos_x: posX,
      pos_y: posY,
      type: transformation.type,
      disabled: transformation.state === RevisionState.DISABLED
    };

    for (const io of transformation.io_interface.inputs) {
      component.inputs.push({
        uuid: `${uuid}_${io.id}`,
        data_type: io.data_type,
        name: io.name === undefined ? '' : io.name,
        input: true,
        pos_x: null,
        pos_y: null,
        constant: false,
        value: ''
      });
    }
    for (const io of transformation.io_interface.outputs) {
      component.outputs.push({
        uuid: `${uuid}_${io.id}`,
        data_type: io.data_type,
        name: io.name === undefined ? '' : io.name,
        input: false,
        pos_x: null,
        pos_y: null,
        constant: false,
        value: ''
      });
    }
    return component;
  }
}
