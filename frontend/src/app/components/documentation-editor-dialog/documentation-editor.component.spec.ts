import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';
import { DocumentationEditorComponent } from './documentation-editor.component';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Transformation } from '../../model/transformation';
import { RevisionState } from '../../enums/revision-state';
import { TransformationType } from '../../enums/transformation-type';
import { selectTransformationState } from '../../store/transformation/transformation.selectors';

describe('DocumentationEditorComponent', () => {
  let component: DocumentationEditorComponent;
  let fixture: ComponentFixture<DocumentationEditorComponent>;

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [
          FormsModule,
          HttpClientModule,
          StoreModule.forRoot(appReducers)
        ],
        declarations: [DocumentationEditorComponent],
        providers: [provideMockStore()]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    const transformation: Transformation = {
      id: 'mockId0',
      revision_group_id: 'mockGroupId',
      name: 'mock0',
      description: 'mock description',
      category: 'EXAMPLES',
      version_tag: '0.0.1',
      released_timestamp: new Date().toISOString(),
      disabled_timestamp: new Date().toISOString(),
      state: RevisionState.DRAFT,
      type: TransformationType.COMPONENT,
      documentation: 'mock documentation',
      content: 'python code',
      io_interface: {
        inputs: [],
        outputs: []
      },
      test_wiring: {
        input_wirings: [],
        output_wirings: []
      }
    };
    const mockStore = TestBed.inject(MockStore);
    mockStore.overrideSelector(selectTransformationState, {
      ids: ['mockId0'],
      entities: { mockId0: transformation }
    });
    fixture = TestBed.createComponent(DocumentationEditorComponent);
    component = fixture.componentInstance;
    component.itemId = 'mockId0';
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
