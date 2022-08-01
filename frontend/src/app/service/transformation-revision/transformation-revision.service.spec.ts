import { TestBed } from '@angular/core/testing';

import { TransformationRevisionService } from './transformation-revision.service';

describe('TransformationRevisionService', () => {
  let service: TransformationRevisionService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TransformationRevisionService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
