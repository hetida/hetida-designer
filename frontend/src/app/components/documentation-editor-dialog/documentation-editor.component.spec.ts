import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { StoreModule } from '@ngrx/store';
import { appReducers } from 'src/app/store/app.reducers';
import { DocumentationEditorComponent } from './documentation-editor.component';

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
        declarations: [DocumentationEditorComponent]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    fixture = TestBed.createComponent(DocumentationEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  xit('should create', () => {
    expect(component).toBeTruthy();
  });
});
