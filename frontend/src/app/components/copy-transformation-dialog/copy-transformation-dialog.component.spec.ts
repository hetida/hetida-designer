import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { BasicTestModule } from 'src/app/basic-test.module';
import { ErrorVisualDirective } from 'src/app/directives/error-visual.directive';
import { TransformationType } from 'src/app/enums/transformation-type';
import { RevisionState } from 'src/app/enums/revision-state';
import { CopyTransformationDialogComponent } from './copy-transformation-dialog.component';
import { Transformation } from '../../model/transformation';

// TODO fix test
describe('CopyBaseItemDialogComponent', () => {
  let component: CopyTransformationDialogComponent;
  let fixture: ComponentFixture<CopyTransformationDialogComponent>;

  const mockAbstractBaseItem: Transformation = {
    id: 'MockId1',
    name: 'Mock',
    tag: 'Mock',
    inputs: [],
    outputs: [],
    type: TransformationType.COMPONENT,
    category: 'Mock Category',
    description: 'Mock Descr',
    groupId: 'g123',
    state: RevisionState.DRAFT,
    wirings: []
  };

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [BasicTestModule, FormsModule, ReactiveFormsModule],
        declarations: [CopyTransformationDialogComponent, ErrorVisualDirective],
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
                type: TransformationType.COMPONENT,
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
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(CopyTransformationDialogComponent);
    const mockStore = TestBed.inject(MockStore);
    // mockStore.overrideSelector(selectAbstractBaseItems, [mockAbstractBaseItem]);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
