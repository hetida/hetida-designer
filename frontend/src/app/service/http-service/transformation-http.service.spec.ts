import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { TransformationHttpService } from './transformation-http.service';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';

describe('TransformationHttpService', () => {
  let transformationHttpService: TransformationHttpService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
      ]
    });
    transformationHttpService = TestBed.inject(TransformationHttpService);
  });

  it('should be created', () => {
    expect(transformationHttpService).toBeTruthy();
  });
});
