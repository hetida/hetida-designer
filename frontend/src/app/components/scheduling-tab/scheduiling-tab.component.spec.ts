import { HttpClient } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';
import { BasicTestModule } from 'src/app/basic-test.module';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';
import { SchedulingTabComponent } from './scheduling-tab.component';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';
import { ImportTrafosButtonComponent } from '../import-trafo/import-trafos-button.component';
import { ImportDialogComponent } from '../import-trafo/import-trafo-dialog.component';

describe('SchedulingTabComponent', () => {
  let component: SchedulingTabComponent;
  let fixture: ComponentFixture<SchedulingTabComponent>;

  const mockTransformationActionService = jasmine.createSpy();
  const mockTabItemService = jasmine.createSpy();
  const httpClientSpy = jasmine.createSpyObj('HttpClient', ['get']);
  const mockMatDialog = jasmine.createSpyObj('MatDialog', ['open']);

  beforeEach(waitForAsync(() => {
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
        },
        {
          provide: MatDialog,
          useValue: mockMatDialog
        }
      ],
      declarations: [
        SchedulingTabComponent,
        ImportTrafosButtonComponent,
        ImportDialogComponent
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    const mockStore = TestBed.inject(MockStore);
    mockStore.overrideSelector(selectHashedTransformationLookupById, {});
    httpClientSpy.get.and.returnValue(of('1.0'));
    fixture = TestBed.createComponent(SchedulingTabComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
