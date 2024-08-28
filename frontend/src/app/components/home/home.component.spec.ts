import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { HomeComponent } from './home.component';
import { BasicTestModule } from 'src/app/basic-test.module';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { StoreModule } from '@ngrx/store';
import { AuthService } from 'src/app/auth/auth.service';
import { appReducers } from 'src/app/store/app.reducers';
import { HomeTabComponent } from '../home-tab/home-tab.component';
import { AppComponent } from 'src/app/app.component';
import { ToolbarComponent } from '../toolbar/toolbar.component';
import { NavigationContainerComponent } from '../navigation/navigation-container/navigation-container.component';
import { ComponentEditorComponent } from '../component-editor/component-editor.component';
import { ContentViewComponent } from '../content-view/content-view.component';
import { NavigationCategoryComponent } from '../navigation/navigation-category/navigation-category.component';
import { NavigationItemComponent } from '../navigation/navigation-item/navigation-item.component';
import { PopoverTransformationComponent } from '../popover-transformation/popover-transformation.component';
import { ProtocolViewerComponent } from '../protocol-viewer/protocol-viewer.component';
import { WorkflowEditorComponent } from '../workflow-editor/workflow-editor.component';
import { ConfigService } from '../../service/configuration/config.service';
import { of } from 'rxjs';

class AuthServiceStub {
  public isAuthEnabled(): boolean {
    return false;
  }

  public isAuthenticated$() {
    return of(false);
  }

  public userName$() {
    return of('testuser');
  }

  public logout() {}
}

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;
  let mockConfigService: jasmine.SpyObj<ConfigService>;

  const createConfigServiceMock = () =>
    jasmine.createSpyObj<ConfigService>('ConfigService', {
      getConfig: of({
        apiEndpoint: '/api'
      })
    });

  beforeEach(waitForAsync(() => {
    mockConfigService = createConfigServiceMock();

    TestBed.configureTestingModule({
      imports: [
        BasicTestModule,
        FormsModule,
        ReactiveFormsModule,
        NgHetidaFlowchartModule,
        MonacoEditorModule,
        StoreModule.forRoot(appReducers),
        HttpClientTestingModule,
        RouterTestingModule
      ],
      providers: [
        {
          provide: AuthService,
          useClass: AuthServiceStub
        },
        {
          provide: ConfigService,
          useValue: mockConfigService
        }
      ],
      declarations: [
        AppComponent,
        HomeComponent,
        HomeTabComponent,
        ToolbarComponent,
        NavigationContainerComponent,
        NavigationCategoryComponent,
        NavigationItemComponent,
        ContentViewComponent,
        ProtocolViewerComponent,
        PopoverTransformationComponent,
        ComponentEditorComponent,
        WorkflowEditorComponent
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create home', () => {
    expect(component).toBeTruthy();
  });
});
