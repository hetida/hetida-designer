import { TestBed } from '@angular/core/testing';

import { TransformationService } from './transformation.service';

describe('TransformationService', () => {
  let service: TransformationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TransformationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
