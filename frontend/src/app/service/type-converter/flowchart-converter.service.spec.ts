import { TestBed } from '@angular/core/testing';
import { IOType, IOTypeOption } from 'hetida-flowchart';
import { RevisionState } from 'src/app/enums/revision-state';
import { TransformationType } from 'src/app/enums/transformation-type';
import { Transformation } from 'src/app/model/transformation';
import { FlowchartConverterService } from './flowchart-converter.service';

describe('FlowchartConverterService', () => {
  let service: FlowchartConverterService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FlowchartConverterService);
  });

  it('convertComponentToFlowchart should preview a workflow stub from its io_interface', () => {
    // stubs lack content, test_wiring and documentation, see isFullTransformation
    const workflowStub = {
      id: 'mockWorkflowId',
      revision_group_id: 'mockWorkflowGroupId',
      name: 'mock workflow',
      category: 'EXAMPLES',
      version_tag: '1.0.0',
      state: RevisionState.RELEASED,
      type: TransformationType.WORKFLOW,
      io_interface: {
        inputs: [
          {
            id: 'mockInputId',
            name: 'series',
            data_type: IOType.SERIES,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: [
          {
            id: 'mockOutputId',
            name: 'result',
            data_type: IOType.FLOAT
          }
        ]
      }
    } as Transformation;

    const preview = service.convertComponentToFlowchart(workflowStub);

    expect(preview.components.length).toBe(1);
    const [component] = preview.components;
    expect(component.name).toBe('mock workflow');
    expect(component.inputs.map(input => input.name)).toEqual(['series']);
    expect(component.outputs.map(output => output.name)).toEqual(['result']);
  });
});
