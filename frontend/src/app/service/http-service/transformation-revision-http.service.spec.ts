import { TestBed } from '@angular/core/testing';

import { TransformationRevisionHttpService } from './transformation-revision-http.service';

describe('TransformationRevisionHttpService', () => {
  let service: TransformationRevisionHttpService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TransformationRevisionHttpService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
