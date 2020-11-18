import { HttpClientModule } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { StoreModule } from '@ngrx/store';
import { appReducers } from '../store/app.reducers';
import { WorkflowEditorService } from './workflow-editor.service';

describe('WorkflowEditorService', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      imports: [HttpClientModule, StoreModule.forRoot(appReducers)]
    })
  );

  it('should be created', () => {
    const service: WorkflowEditorService = TestBed.inject(
      WorkflowEditorService
    );
    expect(service).toBeTruthy();
  });
});
