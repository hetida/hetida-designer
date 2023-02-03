import { HttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';
import { BasicTestModule } from 'src/app/basic-test.module';
import { BaseItemActionService } from 'src/app/service/transformation/transformation-action.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { HomeComponent } from './home.component';

// TODO fix test
describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;

  const mockBaseItemActionService = jasmine.createSpy();
  const mockTabItemService = jasmine.createSpy();
  const httpClientSpy = jasmine.createSpyObj('HttpClient', ['get']);

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
          },
          {
            provide: HttpClient,
            useValue: httpClientSpy
          }
        ],
        declarations: [HomeComponent]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    const mockStore = TestBed.inject(MockStore);
    // mockStore.overrideSelector(selectHashedAbstractBaseItemLookupById, {});
    httpClientSpy.get.and.returnValue(of('1.0'));
    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
