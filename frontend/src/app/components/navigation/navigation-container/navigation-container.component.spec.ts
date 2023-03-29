import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';
import { BasicTestModule } from 'src/app/basic-test.module';
import { TransformationType } from 'src/app/enums/transformation-type';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TransformationService } from 'src/app/service/transformation/transformation.service';
import { selectTransformationsByCategoryAndName } from 'src/app/store/transformation/transformation.selectors';
import { AuthService } from '../../../auth/auth.service';
import { NavigationCategoryComponent } from '../navigation-category/navigation-category.component';
import { NavigationItemComponent } from '../navigation-item/navigation-item.component';
import { NavigationContainerComponent } from './navigation-container.component';
import { Transformation } from '../../../model/transformation';

describe('NavigationContainerComponent', () => {
  let component: NavigationContainerComponent;
  let fixture: ComponentFixture<NavigationContainerComponent>;

  const mockSelectTransformationsByCategoryAndName: {
    [category: string]: Transformation[];
  } = { test1: [] };

  const mockTransformationService = jasmine.createSpyObj<TransformationService>(
    'TransformationService',
    ['fetchAllTransformations']
  );

  const mockAuthService = jasmine.createSpyObj<AuthService>('AuthService', {
    isAuthenticated$: of(true)
  });

  const mockTransformationActionService = jasmine.createSpy();

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [
          FormsModule,
          ReactiveFormsModule,
          BasicTestModule,
          BrowserAnimationsModule
        ],
        declarations: [
          NavigationContainerComponent,
          NavigationCategoryComponent,
          NavigationItemComponent
        ],
        providers: [
          provideMockStore(),
          {
            provide: TransformationService,
            useValue: mockTransformationService
          },
          {
            provide: TransformationActionService,
            useValue: mockTransformationActionService
          },
          {
            provide: AuthService,
            useValue: mockAuthService
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    const mockStore = TestBed.inject(MockStore);
    mockStore.overrideSelector(
      selectTransformationsByCategoryAndName(TransformationType.COMPONENT),
      mockSelectTransformationsByCategoryAndName
    );
    fixture = TestBed.createComponent(NavigationContainerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
