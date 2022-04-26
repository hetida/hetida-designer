import { Component } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { MonacoEditorModule } from 'ngx-monaco-editor';
import { BasicTestModule } from 'src/app/basic-test.module';
import { TabItemType } from 'src/app/model/tab-item';
import { ComponentEditorComponent } from '../component-editor/component-editor.component';
import { ToolbarComponent } from '../toolbar/toolbar.component';
import { WorkflowEditorComponent } from '../workflow-editor/workflow-editor.component';
import {
  ContentViewComponent,
  selectContentViewStoreState
} from './content-view.component';

@Component({ selector: 'hd-home', template: '' })
class HomeStubComponent {}

describe('ContentViewComponent', () => {
  let component: ContentViewComponent;
  let fixture: ComponentFixture<ContentViewComponent>;

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [
          BasicTestModule,
          FormsModule,
          MonacoEditorModule.forRoot(),
          NgHetidaFlowchartModule
        ],
        declarations: [
          ContentViewComponent,
          ToolbarComponent,
          ComponentEditorComponent,
          WorkflowEditorComponent,
          HomeStubComponent
        ],
        providers: [provideMockStore()]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    const mockStore = TestBed.inject(MockStore);
    mockStore.overrideSelector(selectContentViewStoreState, {
      orderedTabItemsWithBaseItem: [],
      activeTabItem: {
        baseItemId: 'test',
        id: 'testId',
        tabItemType: TabItemType.BASE_ITEM
      }
    });
    fixture = TestBed.createComponent(ContentViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
