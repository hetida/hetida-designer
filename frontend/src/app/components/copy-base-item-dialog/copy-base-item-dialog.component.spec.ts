import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { BasicTestModule } from 'src/app/angular-test.module';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { BaseItemType } from 'src/app/enums/base-item-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { AbstractBaseItem } from 'src/app/model/base-item';
import { selectAbstractBaseItems } from 'src/app/store/base-item/base-item.selectors';
import { CopyBaseItemDialogComponent } from './copy-base-item-dialog.component';

describe('CopyBaseItemDialogComponent', () => {
  let component: CopyBaseItemDialogComponent;
  let fixture: ComponentFixture<CopyBaseItemDialogComponent>;

  const mockAbstractBaseItem: AbstractBaseItem = {
    id: 'MockId1',
    name: 'Mock',
    tag: 'Mock',
    inputs: [],
    outputs: [],
    type: BaseItemType.COMPONENT,
    category: 'Mock Category',
    description: 'Mock Descr',
    groupId: 'g123',
    state: RevisionState.DRAFT,
    wirings: []
  };

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [BasicTestModule, FormsModule, ReactiveFormsModule],
      declarations: [CopyBaseItemDialogComponent, ErrorVisualDirective],
      providers: [
        provideMockStore({}),
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            title: 'MOCK',
            content: 'MOCK',
            actionOk: 'MOCK',
            actionCancel: 'MOCK',
            abstractBaseItem: {
              id: 'MockId1',
              name: 'Mock',
              tag: 'Mock',
              pos_x: null,
              pos_y: null,
              inputs: [],
              outputs: [],
              links: [],
              type: BaseItemType.COMPONENT,
              groupId: 'g123'
            },
            disabledState: {
              name: true,
              category: true,
              tag: true,
              description: true
            }
          }
        },
        { provide: MatDialogRef, useValue: {} }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CopyBaseItemDialogComponent);
    const mockStore = TestBed.inject(MockStore);
    mockStore.overrideSelector(selectAbstractBaseItems, [mockAbstractBaseItem]);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
