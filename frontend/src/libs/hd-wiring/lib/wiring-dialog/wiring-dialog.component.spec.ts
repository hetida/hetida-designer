import { CommonModule } from '@angular/common';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { Component, EventEmitter } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormGroup, FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogRef
} from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { IOType, IOTypeOption } from 'hetida-flowchart';
import { of } from 'rxjs';
import {
  Adapter,
  AdapterDataType,
  AdapterHttpService,
  SourceSinkNode
} from '../adapter-http.service';
import { MaterialModule } from '../material.module';
import { NodeClickEvent } from '../node-click/node-click';
import { WiringChangeEvent } from '../node-wiring-context-menu';
import {
  UiItemWiring,
  WiringDialogComponent,
  WiringItem
} from './wiring-dialog.component';

@Component({
  selector: 'hd-tree-node-modal',
  template: '',
  standalone: false
})
class TestTreeNodeModalComponent {
  // Arrange
  nodeClickEvent: NodeClickEvent = {
    event: {
      clientX: 0,
      clientY: 0
    } as any,
    adapterUrl: 'dummyUrl',
    nodeSourceType: 'SOURCE',
    node: {
      id: 'testNodeId1',
      expandable: false,
      level: 0,
      loading: false,
      name: 'testNodeFromEvent',
      parentId: 'oneThingNodeId',
      path: 'Plant A / Pickling Unit / Influx',
      thingNodeId: 'oneThingNodeId',
      type: AdapterDataType.STRING
    }
  };
  nodeClick = of(this.nodeClickEvent);

  wiringChangeEvent: WiringChangeEvent = {
    checked: true,
    ioItemId: 'mockInput1Id'
  };
  wiringChange = of(this.wiringChangeEvent);

  nodeMetaDataClick = new EventEmitter();
}

describe('WiringDialogComponent', () => {
  // Arrange
  let component: WiringDialogComponent;
  let fixture: ComponentFixture<WiringDialogComponent>;
  let mockMatDialog: MatDialog;
  const mockAdapterService = jasmine.createSpyObj<AdapterHttpService>(
    'AdapterHttpService',
    ['getNodesOfAdapter', 'getOneSource']
  );

  beforeEach(waitForAsync(() => {
    const mockTransformation: WiringItem = {
      id: 'mockWiringId1',
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      },
      io_interface: {
        inputs: [
          {
            id: 'mockInput1Id',
            name: 'mockInput1',
            data_type: IOType.STRING,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: []
      },
      name: 'mockWiring',
      version_tag: '1.1.1.mock'
    };

    mockMatDialog = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);

    TestBed.configureTestingModule({
      declarations: [WiringDialogComponent],
      imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        MaterialModule,
        NoopAnimationsModule
      ],
      providers: [
        {
          provide: AdapterHttpService,
          useValue: mockAdapterService
        },
        {
          provide: MatDialog,
          useValue: mockMatDialog
        },
        { provide: MatDialogRef, useValue: {} },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            title: 'test',
            wiringItem: mockTransformation,
            adapterList: []
          }
        },
        provideHttpClient(withInterceptorsFromDi())
      ]
    }).compileComponents();
  }));

  it('should create', () => {
    // Act
    fixture = TestBed.createComponent(WiringDialogComponent);
    component = fixture.componentInstance;
    component.adapterList = [];
    fixture.detectChanges();

    // Assert
    expect(component).toBeTruthy();
  });

  it('input form control created with no wiring', () => {
    // Act
    fixture = TestBed.createComponent(WiringDialogComponent);
    component = fixture.componentInstance;
    component.adapterList = [];
    fixture.detectChanges();

    const formGroup = component.inputFormArray.controls[0] as FormGroup;
    const uiWiring: UiItemWiring = formGroup.getRawValue();

    // Assert
    expect(component.inputFormArray.length).toBe(1);
    expect(uiWiring.ioItemId).toBe('mockInput1Id');
  });

  it('should from control created with manual wiring', () => {
    // the name of io item is used to associate the wiring with his io item
    // wiring.workflowInputName <=> input.name

    // Arrange
    const MOCK_INPUT_WIRING_NAME = 'mockWiringInput';

    const mockTransformation: WiringItem = {
      id: 'mockWiringId1',
      test_wiring: {
        input_wirings: [
          {
            workflow_input_name: MOCK_INPUT_WIRING_NAME,
            adapter_id: 'direct_provisioning',
            ref_id: 'inputWiring1',
            type: AdapterDataType.STRING,
            filters: {
              value: 'testRawValue'
            }
          }
        ],
        output_wirings: []
      },
      io_interface: {
        inputs: [
          {
            id: 'mockInput1Id',
            name: MOCK_INPUT_WIRING_NAME,
            data_type: IOType.STRING,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: []
      },
      name: 'mockWiring',
      version_tag: '1.1.1.mock'
    };

    const data = {
      title: 'test20',
      wiringItem: mockTransformation,
      adapterList: [] as string[]
    };

    // Act
    TestBed.overrideProvider(MAT_DIALOG_DATA, {
      useValue: data
    });

    fixture = TestBed.createComponent(WiringDialogComponent);
    component = fixture.componentInstance;
    component.adapterList = [];
    fixture.detectChanges();

    const formGroup = component.inputFormArray.controls[0] as FormGroup;
    const uiWiring: UiItemWiring = formGroup.getRawValue();

    // Assert
    expect(component.inputFormArray.length).toBe(1);
    expect(uiWiring.ioItemId).toBe('mockInput1Id');
    expect(uiWiring.rawValue).toBe('testRawValue');
  });

  it('should create form control with wiring from adapter', () => {
    // the name of io item is used to associate the wiring with his io item
    // wiring.workflowInputName <=> input.name

    // Arrange
    const MOCK_INPUT_WIRING_NAME = 'mockWiringInput';

    const adapterList: Adapter[] = [
      {
        id: 'testid',
        name: 'my test adapter',
        url: 'https://dummy.de'
      }
    ];

    const mockTransformation: WiringItem = {
      id: 'mockWiringId1',
      test_wiring: {
        input_wirings: [
          {
            workflow_input_name: MOCK_INPUT_WIRING_NAME,
            adapter_id: adapterList[0].id,
            ref_id: 'someNodeId',
            ref_id_type: 'SOURCE',
            type: AdapterDataType.STRING,
            filters: {
              value: 'testRawValue'
            }
          }
        ],
        output_wirings: []
      },
      io_interface: {
        inputs: [
          {
            id: 'mockInput1Id',
            name: MOCK_INPUT_WIRING_NAME,
            data_type: IOType.STRING,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: []
      },
      name: 'mockWiring',
      version_tag: '1.1.1.mock'
    };

    const data = {
      title: 'test20',
      wiringItem: mockTransformation,
      adapterList
    };

    // Act
    TestBed.overrideProvider(MAT_DIALOG_DATA, {
      useValue: data
    });

    mockAdapterService.getOneSource.and.returnValue(
      of({
        id: 'someNodeId',
        name: 'testMockNode',
        thingNodeId: 'oneTestThingNodeId',
        type: AdapterDataType.STRING,
        visible: true,
        path: 'some/test/path'
      })
    );

    const fixtureLocal = TestBed.createComponent(WiringDialogComponent);
    const componentLocal = fixtureLocal.componentInstance;
    componentLocal.adapterList = adapterList;
    fixtureLocal.detectChanges();

    const formGroup = componentLocal.inputFormArray.controls[0] as FormGroup;
    const uiWiring: UiItemWiring = formGroup.getRawValue();

    // Assert
    expect(componentLocal.inputFormArray.length).toBe(1);
    expect(uiWiring.ioItemId).toBe('mockInput1Id');
    expect(uiWiring.nodeId).toBe('someNodeId');
    expect(uiWiring.nodePath).toBe('some/test/path');
    expect(componentLocal._selectionHint(formGroup)).toBe('some/test/path');
    expect(componentLocal._selectionTooltip(formGroup)).toBe(
      'ID: someNodeId\nPath: some/test/path'
    );
  });

  it('should not show a hint if the adapter provides no path', () => {
    // Arrange
    const MOCK_INPUT_WIRING_NAME = 'mockWiringInput';

    const adapterList: Adapter[] = [
      {
        id: 'testid',
        name: 'my test adapter',
        url: 'https://dummy.de'
      }
    ];

    const mockTransformation: WiringItem = {
      id: 'mockWiringId1',
      test_wiring: {
        input_wirings: [
          {
            workflow_input_name: MOCK_INPUT_WIRING_NAME,
            adapter_id: adapterList[0].id,
            ref_id: 'someNodeId',
            ref_id_type: 'SOURCE',
            type: AdapterDataType.STRING,
            filters: {
              value: 'testRawValue'
            }
          }
        ],
        output_wirings: []
      },
      io_interface: {
        inputs: [
          {
            id: 'mockInput1Id',
            name: MOCK_INPUT_WIRING_NAME,
            data_type: IOType.STRING,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: []
      },
      name: 'mockWiring',
      version_tag: '1.1.1.mock'
    };

    // Act
    TestBed.overrideProvider(MAT_DIALOG_DATA, {
      useValue: {
        title: 'test20',
        wiringItem: mockTransformation,
        adapterList
      }
    });

    // the path attribute is optional for generic rest adapters
    mockAdapterService.getOneSource.and.returnValue(
      of({
        id: 'someNodeId',
        name: 'testMockNode',
        thingNodeId: 'oneTestThingNodeId',
        type: AdapterDataType.STRING,
        visible: true
      } as SourceSinkNode)
    );

    const fixtureLocal = TestBed.createComponent(WiringDialogComponent);
    const componentLocal = fixtureLocal.componentInstance;
    componentLocal.adapterList = adapterList;
    fixtureLocal.detectChanges();

    const formGroup = componentLocal.inputFormArray.controls[0] as FormGroup;
    const uiWiring: UiItemWiring = formGroup.getRawValue();

    // Assert
    expect(uiWiring.nodePath).toBeNull();
    expect(componentLocal._selectionHint(formGroup)).toBe('');
    expect(componentLocal._selectionTooltip(formGroup)).toBe('someNodeId');
  });

  it('should offer hint and tooltip for a free text filter', () => {
    // Arrange
    const MOCK_INPUT_WIRING_NAME = 'mockWiringInput';

    const adapterList: Adapter[] = [
      {
        id: 'testid',
        name: 'my test adapter',
        url: 'https://dummy.de'
      }
    ];

    const mockTransformation: WiringItem = {
      id: 'mockWiringId1',
      test_wiring: {
        input_wirings: [
          {
            workflow_input_name: MOCK_INPUT_WIRING_NAME,
            adapter_id: adapterList[0].id,
            ref_id: 'someNodeId',
            ref_id_type: 'SOURCE',
            type: AdapterDataType.STRING,
            filters: {}
          }
        ],
        output_wirings: []
      },
      io_interface: {
        inputs: [
          {
            id: 'mockInput1Id',
            name: MOCK_INPUT_WIRING_NAME,
            data_type: IOType.STRING,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: []
      },
      name: 'mockWiring',
      version_tag: '1.1.1.mock'
    };

    // Act
    TestBed.overrideProvider(MAT_DIALOG_DATA, {
      useValue: {
        title: 'test20',
        wiringItem: mockTransformation,
        adapterList
      }
    });

    mockAdapterService.getOneSource.and.returnValue(
      of({
        id: 'someNodeId',
        name: 'testMockNode',
        thingNodeId: 'oneTestThingNodeId',
        type: AdapterDataType.STRING,
        visible: true,
        path: 'some/test/path',
        filters: {
          frequency: {
            name: 'frequency',
            type: 'free_text',
            required: false,
            default_value: '5min',
            description: 'resampling frequency'
          },
          offset: {
            name: 'offset',
            type: 'free_text',
            required: false
          }
        }
      } as unknown as SourceSinkNode)
    );

    const fixtureLocal = TestBed.createComponent(WiringDialogComponent);
    const componentLocal = fixtureLocal.componentInstance;
    componentLocal.adapterList = adapterList;
    fixtureLocal.detectChanges();

    const formGroup = componentLocal.inputFormArray.controls[0] as FormGroup;
    const filterControls = componentLocal._textFiltersFormArray(formGroup)
      .controls as FormGroup[];
    const frequencyFilter = filterControls[0];
    const offsetFilter = filterControls[1];

    // Assert
    expect(frequencyFilter.get('value_frequency')?.value).toBe('5min');
    expect(componentLocal._filterHint(frequencyFilter)).toBe(
      'resampling frequency'
    );
    expect(componentLocal._filterTooltip(frequencyFilter)).toBe(
      'Default: 5min\nresampling frequency'
    );

    // a filter without default value and description has nothing to show
    expect(componentLocal._filterHint(offsetFilter)).toBe('');
    expect(componentLocal._filterTooltip(offsetFilter)).toBe('');
  });

  it('should create form control with io item | wire to a source node', () => {
    // the name of io item is used to associate the wiring with his io item
    // wiring.workflowInputName <=> input.name

    // Arrange
    const MOCK_INPUT_WIRING_NAME = 'mockWiringInput';

    const adapterList: Adapter[] = [
      {
        id: 'direct_provisioning',
        name: 'my test adapter',
        url: 'https://dummy.de'
      }
    ];

    const mockTransformation: WiringItem = {
      id: 'mockWiringId1',
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      },
      io_interface: {
        inputs: [
          {
            id: 'mockInput1Id',
            name: MOCK_INPUT_WIRING_NAME,
            data_type: IOType.STRING,
            type: IOTypeOption.REQUIRED
          }
        ],
        outputs: []
      },
      name: 'mockWiring',
      version_tag: '1.1.1.mock'
    };

    const data = {
      title: 'test20',
      wiringItem: mockTransformation,
      adapterList
    };

    // Act
    TestBed.overrideProvider(MAT_DIALOG_DATA, {
      useValue: data
    });

    const testTreeNodeModalComponent = new TestTreeNodeModalComponent();

    TestBed.overrideProvider(MatDialog, {
      useValue: {
        open: () => {
          return {
            componentInstance: testTreeNodeModalComponent
          };
        }
      }
    });

    const fixtureLocal = TestBed.createComponent(WiringDialogComponent);
    const componentLocal = fixtureLocal.componentInstance;
    componentLocal.adapterList = adapterList;
    fixtureLocal.detectChanges();

    let formGroup = componentLocal.inputFormArray.controls[0] as FormGroup;
    let uiWiring: UiItemWiring = formGroup.getRawValue();

    componentLocal._openAdapterTreeDialog(
      'SOURCE',
      IOType.STRING,
      adapterList[0].id,
      'INPUT_WIRING'
    );
    formGroup = componentLocal.inputFormArray.controls[0] as FormGroup;
    uiWiring = formGroup.getRawValue();

    // Assert
    expect(componentLocal.inputFormArray.length).toBe(1);
    expect(uiWiring.ioItemId).toBe('mockInput1Id');
    expect(uiWiring.adapterId).toBe(adapterList[0].id);
    expect(uiWiring.nodeId).toBe('testNodeId1');
    expect(uiWiring.nodePath).toBe('Plant A / Pickling Unit / Influx');
    expect(componentLocal._selectionHint(formGroup)).toBe(
      'Plant A / Pickling Unit / Influx'
    );
  });
});
