import { TestBed } from '@angular/core/testing';

import { TransformationHttpService } from './transformation-http.service';

describe('TransformationHttpService', () => {
  let service: TransformationHttpService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TransformationHttpService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
