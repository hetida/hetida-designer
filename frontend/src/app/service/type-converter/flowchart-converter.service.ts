import { Injectable } from '@angular/core';
import {
  FlowchartComponent,
  FlowchartComponentIO,
  FlowchartComponentLink,
  FlowchartConfiguration,
  IOTypeOption
} from 'hetida-flowchart';
import { RevisionState } from 'src/app/enums/revision-state';
import { Connector } from 'src/app/model/connector';
import { Position } from 'src/app/model/position';
import { v4 as UUID } from 'uuid';
import {
  Transformation,
  WorkflowTransformation
} from '../../model/transformation';
import { Operator } from 'src/app/model/operator';
import { Constant } from 'src/app/model/constant';
import { VertexIds } from 'src/app/components/workflow-editor/workflow-editor.component';
import { Utils } from 'src/app/utils/utils';

@Injectable({
  providedIn: 'root'
})
export class FlowchartConverterService {
  // TODO rename to convertTransformationToFlowchartForPreview?
  /**
   * converts the given transformation to a flowchart configuration
   * @param transformation given transformation
   */
  public convertComponentToFlowchart(
    transformation: Transformation
  ): FlowchartConfiguration {
    const operator = {
      ...transformation,
      transformation_id: transformation.id,
      inputs: transformation.io_interface.inputs
        .map(input => {
          if (typeof transformation.content !== 'string') {
            const inputConnector = transformation.content.inputs.filter(
              contentInput => contentInput.id === input.id
            );
            if (inputConnector.length > 0) {
              transformation.content.operators
                .filter(opt => opt.id === inputConnector[0].operator_id)
                .forEach(foundOperator => {
                  foundOperator.inputs.forEach(operatorInput => {
                    if (operatorInput.id === inputConnector[0].connector_id) {
                      input.exposed = false;
                      input.type = inputConnector[0].type;
                    }
                  });
                });
            }
          }
          return input;
        })
        .map(input => {
          return {
            ...input,
            exposed: input.exposed,
            is_default_value: input.type === IOTypeOption.OPTIONAL,
            position: null
          };
        }),
      outputs: transformation.io_interface.outputs.map(output => ({
        ...output,
        position: null
      }))
    };
    const flowchartOperator = this.convertOperatorToFlowchartOperator(
      operator,
      0,
      0
    );
    return {
      id: '',
      components: [flowchartOperator],
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
    const workflowClean = Utils.deepCopy(workflow);
    workflowClean.content.inputs = workflowClean.content.inputs.filter(
      io => io.name !== '' && io.name !== null && io.name !== undefined
    );
    workflowClean.content.outputs = workflowClean.content.outputs.filter(
      io => io.name !== '' && io.name !== null && io.name !== undefined
    );

    const flowchart = {
      id: workflow.id,
      components:
        this.convertWorkflowOperatorsToFlowchartComponents(workflowClean),
      io: this.convertWorkflowIOToFlowchartIO(workflowClean),
      links: this.convertWorkflowLinksToFlowchartLinks(workflowClean)
    } as FlowchartConfiguration;

    this.convertWorkflowConstants(workflowClean, flowchart);

    return flowchart;
  }

  private convertWorkflowConstants(
    workflow: WorkflowTransformation,
    flowchart: FlowchartConfiguration
  ): void {
    const convertConstant = (constant: Constant, isInput: boolean) => {
      if (constant === undefined) {
        return;
      }
      if (
        constant.operator_id === undefined ||
        constant.connector_id === undefined
      ) {
        return;
      }
      const component = flowchart.components.find(
        flowchartComponent => flowchartComponent.uuid === constant.operator_id
      );
      if (component === undefined) {
        return;
      }
      const connector = (isInput ? component.inputs : component.outputs).find(
        input =>
          input.uuid === `${constant.operator_id}_${constant.connector_id}`
      );
      if (connector === undefined) {
        return;
      }
      connector.constant = true;
      connector.value = constant.value;

      // TODO: Maybe links to constants can be removed from the API completely, since they are deleted here anyway, HDOS-487.
      flowchart.links = flowchart.links.filter(
        link =>
          (isInput ? link.to : link.from) !==
          `link-${constant.operator_id}_${constant.connector_id}`
      );
    };

    for (const constant of workflow.content.constants) {
      convertConstant(constant, true);
    }
    for (const constant of workflow.content.constants) {
      convertConstant(constant, false);
    }
  }

  /**
   * converts all operators of the given workflow to flowchart components
   * @param workflow given workflow
   */
  private convertWorkflowOperatorsToFlowchartComponents(
    workflow: WorkflowTransformation
  ): FlowchartComponent[] {
    const components: Array<FlowchartComponent> = [];

    for (const operator of workflow.content.operators) {
      components.push(
        this.convertOperatorToFlowchartOperator(
          operator,
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
      workflowIO.push({
        uuid: `${workflow.id}_${io.id}`,
        data_type: io.data_type,
        name: io.name === undefined ? '' : io.name,
        input: false,
        pos_x: io.position.x,
        pos_y: io.position.y,
        constant: false,
        value: '',
        is_default_value: io.type === IOTypeOption.OPTIONAL
      });
    }

    for (const io of workflow.content.outputs) {
      workflowIO.push({
        uuid: `${workflow.id}_${io.id}`,
        data_type: io.data_type,
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
      const linkPath = link.path.map(position => [position.x, position.y]);
      const linkIds = link.path.map(() => UUID().toString());

      /**
       * Links which lead to an input / output of the workflow itself do not have a start / end operator id
       * (since the operator is not part of the workflow content but it is the workflow itself).
       * The flowchart however needs an operator id for every link,
       * that is why we use the id of the workflow.
       */
      const linkStartOperator = link.start.operator ?? workflow.id;
      const linkEndOperator = link.end.operator ?? workflow.id;

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
   * converts the svg path data and the id's of the position to a position array
   * @param link svg link element
   */
  public convertLinkPathToPositions(link: Element): Position[] {
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
    return coordinates.map(coords => ({
      x: coords[0],
      y: coords[1]
    }));
  }

  /**
   * extracts the operator and connector id from the given link element
   * @param link given link element
   * @param from if the start (true) or the end (false) operator and connectors should be extracted
   */
  public getLinkOperatorAndConnectorId(
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

  /**
   * Extract the connector from the operator or workflow given the vertex ids.
   * @param vertexIds given linkSourceIds or linkTargetIds
   * @param workflowTransformation current workflow
   * @param searchInWorkflowIoInterface if true, search for the connector in the workflow io interface
   * instead of the workflow content operators
   */
  public getConnectorFromOperatorById(
    vertexIds: VertexIds,
    workflowTransformation: WorkflowTransformation,
    searchInWorkflowIoInterface: boolean
  ): Connector {
    let foundConnector: Connector;

    if (searchInWorkflowIoInterface) {
      const ios = [
        ...workflowTransformation.io_interface.inputs,
        ...workflowTransformation.io_interface.outputs
      ];

      const foundIo = ios.find(io => io.id === vertexIds.connectorId);

      foundConnector = {
        ...foundIo,
        position: { x: 0, y: 0 }
      };
    } else {
      const foundOperator = workflowTransformation.content.operators.find(
        operator => operator.id === vertexIds.operatorId
      );
      const connectors = [...foundOperator.inputs, ...foundOperator.outputs];

      foundConnector = connectors.find(
        connector => connector.id === vertexIds.connectorId
      );
    }

    return foundConnector;
  }

  // noinspection JSMethodCanBeStatic
  /**
   * converts a operator to a flowchart operator, if no position is given, it will create a new operator
   * @param operator given operator
   * @param posX x coordinate of the operator
   * @param posY y coordinate of the operator
   */
  private convertOperatorToFlowchartOperator(
    operator: Omit<Operator, 'position'>,
    posX: number,
    posY: number
  ): FlowchartComponent {
    let uuid: string;
    if (posX === null && posY === null) {
      uuid = UUID().toString();
    } else {
      uuid = operator.id;
    }
    const component: FlowchartComponent = {
      uuid,
      name: operator.name,
      revision: operator.version_tag,
      inputs: [],
      outputs: [],
      pos_x: posX,
      pos_y: posY,
      type: operator.type,
      disabled: operator.state === RevisionState.DISABLED
    };

    for (const io of operator.inputs) {
      const isDefaultValue = io.type === IOTypeOption.OPTIONAL;
      component.inputs.push({
        uuid: `${uuid}_${io.id}`,
        data_type: io.data_type,
        name: io.name === undefined ? '' : io.name,
        input: true,
        pos_x: null,
        pos_y: null,
        constant: false,
        exposed: io.exposed,
        is_default_value: isDefaultValue,
        value: isDefaultValue && io.value ? io.value : ''
      });
    }
    for (const io of operator.outputs) {
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
