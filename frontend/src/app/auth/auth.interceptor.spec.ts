import {
  HTTP_INTERCEPTORS,
  HttpClient,
  HttpContext
} from '@angular/common/http';
import {
  HttpClientTestingModule,
  HttpTestingController
} from '@angular/common/http/testing';
import { inject, TestBed } from '@angular/core/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';
import { ConfigService } from '../service/configuration/config.service';

import { AuthInterceptor, BYPASS_AUTH } from './auth.interceptor';

describe('AuthInterceptor', () => {
  let mockConfigService: jasmine.SpyObj<ConfigService>;

  const createConfigServiceMock = () =>
    jasmine.createSpyObj<ConfigService>('ConfigService', ['getConfig']);

  const mockSecurityService = jasmine.createSpyObj<OidcSecurityService>(
    'OidcSecurityService',
    { getAccessToken: of('test-token') }
  );

  beforeEach(() => {
    mockConfigService = createConfigServiceMock();
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        AuthInterceptor,
        {
          provide: ConfigService,
          useValue: mockConfigService
        },
        {
          provide: OidcSecurityService,
          useValue: mockSecurityService
        },
        {
          provide: HTTP_INTERCEPTORS,
          useClass: AuthInterceptor,
          multi: true
        }
      ]
    });
  });

  it('should be created', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/test',
        authEnabled: false
      })
    );
    const interceptor: AuthInterceptor = TestBed.inject(AuthInterceptor);
    expect(interceptor).toBeTruthy();
  });

  it('token should not be added if auth is disabled', inject(
    [HttpClient, HttpTestingController],
    (http: HttpClient, httpMock: HttpTestingController) => {
      mockConfigService.getConfig.and.returnValue(
        of({
          apiEndpoint: '/api',
          authEnabled: false
        })
      );
      http.get('/base-items').subscribe(response => {
        expect(response).toBeTruthy();
      });

      const testRequest = httpMock.expectOne(
        request => !request.headers.has('Authorization')
      );
      testRequest.flush({ items: [] });
      httpMock.verify();
    }
  ));

  it('token should be added if auth is enabled', inject(
    [HttpClient, HttpTestingController],
    (http: HttpClient, httpMock: HttpTestingController) => {
      mockConfigService.getConfig.and.returnValue(
        of({
          apiEndpoint: '/api',
          authEnabled: true
        })
      );
      http.get('/base-items').subscribe(response => {
        expect(response).toBeTruthy();
      });

      const testRequest = httpMock.expectOne(
        request =>
          request.headers.has('Authorization') &&
          request.headers.get('Authorization') === 'Bearer test-token'
      );

      testRequest.flush({ hello: 'world' });
      httpMock.verify();
    }
  ));

  it('token should not be added if BYPASS_AUTH context is set', inject(
    [HttpClient, HttpTestingController],
    (http: HttpClient, httpMock: HttpTestingController) => {
      mockConfigService.getConfig.and.returnValue(
        of({
          apiEndpoint: '/api',
          authEnabled: true
        })
      );
      http
        .get('/base-items', {
          context: new HttpContext().set(BYPASS_AUTH, true)
        })
        .subscribe(response => {
          expect(response).toBeTruthy();
        });

      const testRequest = httpMock.expectOne(
        request => !request.headers.has('Authorization')
      );
      testRequest.flush({ items: [] });
      httpMock.verify();
    }
  ));
});
