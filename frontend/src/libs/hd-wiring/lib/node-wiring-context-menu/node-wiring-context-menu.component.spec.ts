import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { IOType, IOTypeOption } from 'hetida-flowchart';
import { AdapterDataType } from '../adapter-http.service';
import { TreeNodeWithUiInfo } from '../node-click/node-click';
import { UiItemWiring } from '../wiring-dialog/wiring-dialog.component';
import { NodeWiringContextMenuComponent } from './node-wiring-context-menu.component';
import { MaterialModule } from '../material.module';

describe('ExecutionDialogContextMenuComponent', () => {
  const mockIOItemWiring: UiItemWiring[] = [
    {
      ioItemName: 'testName',
      ioItemId: 'ioItemId',
      rawValue: 'blablub',
      nodeId: 'node1',
      nodeName: 'test',
      nodeType: AdapterDataType.FLOAT,
      ioType: IOType.STRING,
      adapterId: 'dasd',
      displayName: 'calculated value',
      textFilters: [],
      type: IOTypeOption.REQUIRED,
      defaultValue: '',
      useDefaultValue: false
    }
  ];

  const uiNode: TreeNodeWithUiInfo = {
    id: 'id',
    thingNodeId: 'thingnodeid',
    name: 'name',
    parentId: 'thingnodeid',
    type: AdapterDataType.STRING,
    expandable: false,
    level: 0,
    loading: false
  };

  let component: NodeWiringContextMenuComponent;
  let fixture: ComponentFixture<NodeWiringContextMenuComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule, ReactiveFormsModule, MaterialModule],
      declarations: [NodeWiringContextMenuComponent],
      providers: [
        { provide: MatDialogRef, useValue: {} },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            IOItem: mockIOItemWiring,
            dataOrigin: uiNode
          }
        }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NodeWiringContextMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
