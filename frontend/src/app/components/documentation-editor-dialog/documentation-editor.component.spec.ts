import { HttpClientModule } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { of } from 'rxjs';
import { Documentation } from 'src/app/model/documentation';
import { DocumentationService } from 'src/app/service/documentation/documentation.service';
import { DocumentationEditorComponent } from './documentation-editor.component';

describe('DocumentationEditorComponent', () => {
  let component: DocumentationEditorComponent;
  let fixture: ComponentFixture<DocumentationEditorComponent>;

  const mockDocumentationService = jasmine.createSpyObj<DocumentationService>(
    'DocumentationService',
    ['getDocumentation']
  );

  beforeEach(
    waitForAsync(() => {
      TestBed.configureTestingModule({
        imports: [FormsModule, HttpClientModule],
        declarations: [DocumentationEditorComponent],
        providers: [
          { provide: MatDialogRef, useValue: {} },
          {
            provide: MAT_DIALOG_DATA,
            useValue: {}
          },
          {
            provide: DocumentationService,
            useValue: mockDocumentationService
          }
        ]
      }).compileComponents();
    })
  );

  beforeEach(() => {
    const mockDocumentation: Documentation = {
      document: 'test1',
      id: '1'
    };

    mockDocumentationService.getDocumentation.and.returnValue(
      of(mockDocumentation)
    );
    fixture = TestBed.createComponent(DocumentationEditorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
