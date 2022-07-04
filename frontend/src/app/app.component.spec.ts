import { HttpClientModule } from '@angular/common/http';
import { TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { MonacoEditorModule } from 'ngx-monaco-editor';
import { AppComponent } from './app.component';
import { AuthService } from './auth/auth.service';
import { BasicTestModule } from './basic-test.module';
import { ComponentEditorComponent } from './components/component-editor/component-editor.component';
import { ContentViewComponent } from './components/content-view/content-view.component';
import { HomeComponent } from './components/home/home.component';
import { NavigationCategoryComponent } from './components/navigation/navigation-category/navigation-category.component';
import { NavigationContainerComponent } from './components/navigation/navigation-container/navigation-container.component';
import { NavigationItemComponent } from './components/navigation/navigation-item/navigation-item.component';
import { PopoverBaseItemComponent } from './components/popover-base-item/popover-base-item.component';
import { ProtocolViewerComponent } from './components/protocol-viewer/protocol-viewer.component';
import { ToolbarComponent } from './components/toolbar/toolbar.component';
import { WorkflowEditorComponent } from './components/workflow-editor/workflow-editor.component';
import { appReducers } from './store/app.reducers';

describe('AppComponent', () => {
  const mockAuthService = jasmine.createSpyObj<AuthService>('AuthSerivce', [
    'isAuthenticated$',
    'userName$',
    'logout'
  ]);

  beforeEach(
    waitForAsync(() => {
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
        providers: [
          {
            provide: AuthService,
            useValue: mockAuthService
          }
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
          PopoverBaseItemComponent,
          ComponentEditorComponent,
          WorkflowEditorComponent
        ]
      }).compileComponents();
    })
  );

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  });
});
