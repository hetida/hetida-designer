import { Component, EventEmitter } from '@angular/core';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  AdapterDataType,
  SourceSinkNode,
  ThingNode
} from '../adapter-http.service';
import { TreeNodeComponent } from './tree-node.component';
import { MaterialModule } from '../material.module';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

@Component({
  selector: 'hd-test-host-component',
  template: `
    <hd-tree-node
      [thingNodes]="thingNodes"
      [sourcesOrSinks]="sourcesOrSinks"
      [nodeSourceType]="nodeSourceType"
      [adapterUrl]="adapterUrl"
    ></hd-tree-node>
  `,
  standalone: false
})
class TestHostComponent {
  thingNodes: ThingNode[] = [
    {
      id: '1',
      name: 'test',
      parentId: null,
      description: 'test description'
    },
    {
      id: '2',
      name: 'child',
      parentId: '1',
      description: 'test description'
    }
  ];
  sourcesOrSinks: SourceSinkNode[] = [
    {
      id: 'a',
      name: 'leaf1',
      thingNodeId: '1',
      visible: true,
      type: AdapterDataType.STRING,
      path: 'test/path'
    }
  ];

  nodeSourceType = 'SOURCE';
  adapterUrl = 'https://dummy.de';

  nodeClick = new EventEmitter();
}

describe('TreeNodeComponent', () => {
  let component: TestHostComponent;
  let fixture: ComponentFixture<TestHostComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [TreeNodeComponent, TestHostComponent],
      imports: [
        FormsModule,
        ReactiveFormsModule,
        MaterialModule,
        NoopAnimationsModule
      ],
      providers: [
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestHostComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
