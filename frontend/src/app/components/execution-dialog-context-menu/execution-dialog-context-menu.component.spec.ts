import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { AdapterUiFlatNode } from 'src/app/model/adapter-ui-node';
import { UiItemWiring } from '../execution-dialog/execution-dialog.component';
import { ExecutionDialogContextMenuComponent } from './execution-dialog-context-menu.component';

describe('ExecutionDialogContextMenuComponent', () => {
  const mockIOItemWiring: UiItemWiring[] = [
    {
      id: 'testId',
      ioItemName: 'testName',
      ioItemId: 'ioItemId',
      rawValue: 'blablub',
      nodeId: 'node1',
      dataType: 'STRING',
      isSource: false
    }
  ];

  const uiNode: AdapterUiFlatNode = {
    id: 'id',
    thingNodeId: 'thingnodeid',
    name: 'name',
    parentId: 'thingnodeid',
    dataType: 'STRING',
    dataSourceType: 'source',
    expandable: false,
    level: 0
  };

  let component: ExecutionDialogContextMenuComponent;
  let fixture: ComponentFixture<ExecutionDialogContextMenuComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule, ReactiveFormsModule],
      declarations: [ExecutionDialogContextMenuComponent],
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
    fixture = TestBed.createComponent(ExecutionDialogContextMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
