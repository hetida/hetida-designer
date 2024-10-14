import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot } from '@angular/router';
import { AutoLoginPartialRoutesGuard } from 'angular-auth-oidc-client';
import { of } from 'rxjs';
import { ConfigService } from '../service/configuration/config.service';

import { AuthGuard } from './auth.guard';

describe('AuthGuard', () => {
  let guard: AuthGuard;
  let mockAutoLoginGuard: jasmine.SpyObj<AutoLoginPartialRoutesGuard>;
  let mockConfigService: jasmine.SpyObj<ConfigService>;

  const createAutoLoginGuardMock = () =>
    jasmine.createSpyObj<AutoLoginPartialRoutesGuard>(
      'AutoLoginPartialRoutesGuard',
      ['canActivate']
    );

  const createConfigServiceMock = () =>
    jasmine.createSpyObj<ConfigService>('ConfigService', ['getConfig']);

  beforeEach(() => {
    mockAutoLoginGuard = createAutoLoginGuardMock();
    mockConfigService = createConfigServiceMock();

    TestBed.configureTestingModule({
      providers: [
        {
          provide: ConfigService,
          useValue: mockConfigService
        },
        {
          provide: AutoLoginPartialRoutesGuard,
          useValue: mockAutoLoginGuard
        }
      ]
    });
  });

  it('should be created', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/api',
        authEnabled: false
      })
    );
    guard = TestBed.inject(AuthGuard);
    expect(guard).toBeTruthy();
  });

  it('#canActivate should call AutoLoginPartialRoutesGuard if auth is enabled', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/api',
        authEnabled: true
      })
    );
    guard = TestBed.inject(AuthGuard);
    guard.canActivate({} as ActivatedRouteSnapshot, null);
    expect(mockAutoLoginGuard.canActivate).toHaveBeenCalled();
  });

  it('#canActivate should not call AutoLoginPartialRoutesGuard if auth is disabled', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/api',
        authEnabled: false
      })
    );
    guard = TestBed.inject(AuthGuard);
    guard.canActivate({} as ActivatedRouteSnapshot, null);
    expect(mockAutoLoginGuard.canActivate).not.toHaveBeenCalled();
  });
});
