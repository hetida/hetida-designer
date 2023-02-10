import { HttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';
import { BasicTestModule } from 'src/app/basic-test.module';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { HomeComponent } from './home.component';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';

// TODO fix test
describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;

  const mockTransformationActionService = jasmine.createSpy();
  const mockTabItemService = jasmine.createSpy();
  const httpClientSpy = jasmine.createSpyObj('HttpClient', ['get']);

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [BasicTestModule],
        providers: [
          provideMockStore(),
          {
            provide: TransformationActionService,
            useValue: mockTransformationActionService
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
    mockStore.overrideSelector(selectHashedTransformationLookupById, {});
    httpClientSpy.get.and.returnValue(of('1.0'));
    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
