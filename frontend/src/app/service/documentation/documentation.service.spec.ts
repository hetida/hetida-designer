import { HttpClientModule } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { DocumentationService } from './documentation.service';

describe('Documentation', () => {
  beforeEach(() =>
    TestBed.configureTestingModule({
      imports: [HttpClientModule]
    })
  );

  it('should be created', () => {
    const service: DocumentationService = TestBed.inject(DocumentationService);
    expect(service).toBeTruthy();
  });
});
