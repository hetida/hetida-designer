import { Component, Input } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { IOType } from 'hetida-flowchart';
import {
  NodeSourceType,
  SourceSinkNode,
  ThingNode
} from '../adapter-http.service';
import { MaterialModule } from '../material.module';
import {
  AdapterTreeModalData,
  TreeNodeModalComponent
} from './tree-node-modal.component';

@Component({
  selector: 'hd-tree-node',
  template: '<p>Mock Tree Node</p>',
  standalone: false
})
class MockTreeNodeComponent {
  @Input()
  initialDataTypeFilter!: IOType;

  @Input()
  nodeSourceType!: NodeSourceType;

  @Input()
  thingNodes!: ThingNode[];

  @Input()
  sourcesOrSinks!: SourceSinkNode[];
}

describe('TreeNodeModalComponent', () => {
  let component: TreeNodeModalComponent;
  let fixture: ComponentFixture<TreeNodeModalComponent>;

  const adapterTreeModalData: AdapterTreeModalData = {
    nodeSourceType: 'SINK',
    adapterUrl: '123'
  };

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [MaterialModule],
      declarations: [TreeNodeModalComponent, MockTreeNodeComponent],
      providers: [
        {
          provide: MAT_DIALOG_DATA,
          useValue: adapterTreeModalData
        },
        { provide: MatDialogRef, useValue: {} }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TreeNodeModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
