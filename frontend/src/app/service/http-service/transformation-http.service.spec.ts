import {
  HttpTestingController,
  provideHttpClientTesting
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ConfigService } from '../configuration/config.service';
import { TransformationHttpService } from './transformation-http.service';
import {
  provideHttpClient,
  withInterceptorsFromDi
} from '@angular/common/http';

describe('TransformationHttpService', () => {
  let transformationHttpService: TransformationHttpService;
  let httpTestingController: HttpTestingController;

  beforeEach(() => {
    const mockConfigService = jasmine.createSpyObj<ConfigService>(
      'ConfigService',
      { getConfig: of({ apiEndpoint: '/api' }) }
    );

    TestBed.configureTestingModule({
      imports: [],
      providers: [
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting(),
        { provide: ConfigService, useValue: mockConfigService }
      ]
    });
    transformationHttpService = TestBed.inject(TransformationHttpService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('should be created', () => {
    expect(transformationHttpService).toBeTruthy();
  });

  it('should fetch the workflows containing a transformation', () => {
    let containingWorkflows: unknown;
    transformationHttpService
      .fetchContainingWorkflows('some-id')
      .subscribe(response => (containingWorkflows = response));

    const request = httpTestingController.expectOne(
      '/api/transformations/some-id/containing_workflows'
    );
    expect(request.request.method).toBe('GET');
    request.flush([]);
    expect(containingWorkflows).toEqual([]);
  });

  it('should run pure plot operators when executing transformations', () => {
    transformationHttpService
      .executeTransformation('some-id', {
        input_wirings: [],
        output_wirings: []
      })
      .subscribe();

    const request = httpTestingController.expectOne(
      '/api/transformations/execute'
    );
    expect(request.request.method).toBe('POST');
    expect(request.request.body.run_pure_plot_operators).toBe(true);
    request.flush({});
  });
});
