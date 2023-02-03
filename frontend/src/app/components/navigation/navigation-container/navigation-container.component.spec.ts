import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';
import { BasicTestModule } from 'src/app/basic-test.module';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { BaseItemService } from 'src/app/service/base-item/base-item.service';
import { AuthService } from '../../../auth/auth.service';
import { NavigationCategoryComponent } from '../navigation-category/navigation-category.component';
import { NavigationItemComponent } from '../navigation-item/navigation-item.component';
import { NavigationContainerComponent } from './navigation-container.component';
import { Transformation } from '../../../model/new-api/transformation';

// TODO fix test
describe('NavigationContainerComponent', () => {
  let component: NavigationContainerComponent;
  let fixture: ComponentFixture<NavigationContainerComponent>;

  const abstractBaseItemsByCategory: {
    [category: string]: Transformation[];
  } = { test1: [] };

  const mockBaseItemService = jasmine.createSpyObj<BaseItemService>(
    'BaseItemService',
    ['fetchAllTransformations']
  );

  const mockAuthService = jasmine.createSpyObj<AuthService>('AuthService', {
    isAuthenticated$: of(true)
  });

  const baseItemActionService = jasmine.createSpy();

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
            provide: BaseItemService,
            useValue: mockBaseItemService
          },
          {
            provide: BaseItemActionService,
            useValue: baseItemActionService
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
    // mockStore.overrideSelector(
    //   selectBaseItemsByCategory(BaseItemType.COMPONENT),
    //   abstractBaseItemsByCategory
    // );
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
