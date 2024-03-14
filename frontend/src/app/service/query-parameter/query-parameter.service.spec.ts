import { TestBed } from '@angular/core/testing';
import { QueryParameterService } from './query-parameter.service';
import { RouterTestingModule } from '@angular/router/testing';

describe('QueryParameterService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule]
    });
  });

  it('should be created', () => {
    const service: QueryParameterService = TestBed.inject(
      QueryParameterService
    );
    expect(service).toBeTruthy();
  });
});
