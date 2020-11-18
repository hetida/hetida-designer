import { HttpClientModule } from '@angular/common/http';
import { async, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { MonacoEditorModule } from 'ngx-monaco-editor';
import { BasicTestModule } from './angular-test.module';
import { AppComponent } from './app.component';
import { ComponentEditorComponent } from './components/component-editor/component-editor.component';
import { ContentViewComponent } from './components/content-view/content-view.component';
import { HomeComponent } from './components/home/home.component';
import { NavigationCategoryComponent } from './components/navigation/navigation-category/navigation-category.component';
import { NavigationContainerComponent } from './components/navigation/navigation-container/navigation-container.component';
import { NavigationItemComponent } from './components/navigation/navigation-item/navigation-item.component';
import { PopoverBaseitemComponent } from './components/popover-baseitem/popover-baseitem.component';
import { ProtocolViewerComponent } from './components/protocol-viewer/protocol-viewer.component';
import { ToolbarComponent } from './components/toolbar/toolbar.component';
import { WorkflowEditorComponent } from './components/workflow-editor/workflow-editor.component';
import { appReducers } from './store/app.reducers';

describe('AppComponent', () => {
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [
        BasicTestModule,
        FormsModule,
        ReactiveFormsModule,
        NgHetidaFlowchartModule,
        MonacoEditorModule,
        StoreModule.forRoot(appReducers),
        HttpClientModule
      ],
      declarations: [
        AppComponent,
        HomeComponent,
        ToolbarComponent,
        NavigationContainerComponent,
        NavigationCategoryComponent,
        NavigationItemComponent,
        ContentViewComponent,
        ProtocolViewerComponent,
        PopoverBaseitemComponent,
        ComponentEditorComponent,
        WorkflowEditorComponent
      ]
    }).compileComponents();
  }));

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  });
});
