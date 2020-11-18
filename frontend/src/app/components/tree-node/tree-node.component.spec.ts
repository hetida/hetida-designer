import { Component } from '@angular/core';
import { async, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  DataSourceSink,
  ThingNodes
} from 'src/app/service/http-service/adapter-http.service';
import { TreeNodeComponent } from './tree-node.component';

@Component({
  selector: `hd-test-host-component`,
  template: `
    <hd-tree-node
      [thingNodes]="thingNodes"
      [sourcesOrSinks]="sourcesOrSinks"
      [dataSourceType]="dataSourceType"
    ></hd-tree-node>
  `
})
class TestHostComponent {
  thingNodes: ThingNodes[] = [
    {
      id: '1',
      name: 'test',
      parentId: null
    },
    {
      id: '2',
      name: 'child',
      parentId: '1'
    }
  ];

  sourcesOrSinks: DataSourceSink[] = [
    {
      id: 'a',
      name: 'leaf1',
      thingNodeId: '1',
      dataType: 'STRING'
    }
  ];

  dataSourceType = 'source';
  // nodeClick = new EventEmitter<AdapterUiFlatNode>();
}

describe('TreeNodeComponent', () => {
  // let component: TestHostComponent;
  // let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule, ReactiveFormsModule],
      declarations: [TreeNodeComponent, TestHostComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    // fixture = TestBed.createComponent(TestHostComponent);
    // component = fixture.componentInstance;
    // fixture.detectChanges();
  });

  // it('should create', () => {
  //   expect(component).toBeTruthy();
  // });
});
