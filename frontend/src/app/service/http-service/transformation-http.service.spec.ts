import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TransformationHttpService } from './transformation-http.service';

describe('TransformationHttpService', () => {
  let transformationHttpService: TransformationHttpService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    transformationHttpService = TestBed.inject(TransformationHttpService);
  });

  it('should be created', () => {
    expect(transformationHttpService).toBeTruthy();
  });
});
