import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { StoreModule } from '@ngrx/store';
import { NgHetidaFlowchartModule } from 'ng-hetida-flowchart';
import { appReducers } from 'src/app/store/app.reducers';
import { WorkflowEditorComponent } from './workflow-editor.component';
describe('WorkflowEditorComponent', () => {
  let component: WorkflowEditorComponent;
  let fixture: ComponentFixture<WorkflowEditorComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        NgHetidaFlowchartModule,
        StoreModule.forRoot(appReducers),
        MatIconModule,
        MatDividerModule,
        MatSnackBarModule,
        HttpClientModule,
        MatDialogModule
      ],
      declarations: [WorkflowEditorComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkflowEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
