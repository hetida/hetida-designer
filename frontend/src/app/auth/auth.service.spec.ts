import { HttpClientModule } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { AuthModule, OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';
import { ConfigService } from '../service/configuration/config.service';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;

  const mockSecurityService = jasmine.createSpyObj<OidcSecurityService>(
    'OidcSecurityService',
    ['isAuthenticated$'],
    {
      userData$: of({
        userData: {
          testattribute: 'My User'
        },
        allUserData: [
          {
            configId: 'test',
            userData: null
          }
        ]
      })
    }
  );

  const mockConfigService = jasmine.createSpyObj<ConfigService>(
    'ConfigService',
    ['getConfig']
  );

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule, AuthModule],
      providers: [
        {
          provide: ConfigService,
          useValue: mockConfigService
        },
        {
          provide: OidcSecurityService,
          useValue: mockSecurityService
        }
      ]
    });
  });

  it('should be created', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/test',
        authEnabled: true
      })
    );
    service = TestBed.inject(AuthService);
    expect(service).toBeTruthy();
  });

  it('#userName$ should return the userName depending on the configuration', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/test',
        authEnabled: true,
        authConfig: {
          authority: 'test',
          clientId: 'test',
          userNameAttribute: 'testattribute'
        }
      })
    );
    service = TestBed.inject(AuthService);
    let name;
    service.userName$().subscribe(username => {
      name = username;
    });
    expect(name).toBe('My User');
  });

  it('#userName$ should return "auth not enabled" if auth is disabled', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/test',
        authEnabled: false
      })
    );
    service = TestBed.inject(AuthService);
    let name;
    service.userName$().subscribe(username => {
      name = username;
    });
    expect(name).toBe('auth not enabled');
  });

  it('#userName$ should return "no username" if auth is enabled but userNameAttribute is not found', () => {
    mockConfigService.getConfig.and.returnValue(
      of({
        apiEndpoint: '/test',
        authEnabled: true,
        authConfig: {
          authority: 'test',
          clientId: 'test',
          userNameAttribute: 'wrongAttribute'
        }
      })
    );
    service = TestBed.inject(AuthService);
    let name;
    service.userName$().subscribe(username => {
      name = username;
    });
    expect(name).toBe('no username');
  });
});
