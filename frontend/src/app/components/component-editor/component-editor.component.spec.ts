import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';
import { appReducers } from 'src/app/store/app.reducers';
import { ComponentEditorComponent } from './component-editor.component';
import { TabItemService } from 'src/app/service/tab-item/tab-item.service';

describe('ComponentEditorComponent', () => {
  let component: ComponentEditorComponent;
  let fixture: ComponentFixture<ComponentEditorComponent>;

  const mockTabItemService = jasmine.createSpy();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ComponentEditorComponent],
      imports: [
        FormsModule,
        MonacoEditorModule.forRoot(),
        StoreModule.forRoot(appReducers)
      ],
      providers: [
        provideHttpClient(withInterceptorsFromDi()),
        {
          provide: TabItemService,
          useValue: mockTabItemService
        }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ComponentEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
