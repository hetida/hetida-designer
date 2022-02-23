import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { BasicTestModule } from 'src/app/angular-test.module';
import { BaseItemActionService } from 'src/app/service/base-item/base-item-action.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { selectHashedAbstractBaseItemLookupById } from 'src/app/store/base-item/base-item.selectors';
import { HomeComponent } from './home.component';

xdescribe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;

  const mockBaseItemActionService = jasmine.createSpy();
  const mockTabItemService = jasmine.createSpy();

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [BasicTestModule],
        providers: [
          provideMockStore(),
          {
            provide: BaseItemActionService,
            useValue: mockBaseItemActionService
          },
          {
            provide: TabItemService,
            useValue: mockTabItemService
          }
        ],
        declarations: [HomeComponent]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    const mockStore = TestBed.inject(MockStore);
    mockStore.overrideSelector(selectHashedAbstractBaseItemLookupById, {});
    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
