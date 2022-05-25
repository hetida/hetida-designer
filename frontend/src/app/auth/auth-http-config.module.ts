import { HttpClient } from '@angular/common/http';
import { NgModule } from '@angular/core';
import {
  AuthModule,
  LogLevel,
  StsConfigHttpLoader,
  StsConfigLoader
} from 'angular-auth-oidc-client';
import { of } from 'rxjs';
import { map } from 'rxjs/operators';

// TODO add ConfigService call
export const httpLoaderFactory = () => {
  const config$ = of(true)
    .pipe(
      map(() => {
        return {
          authority: `http://localhost:8080/auth/realms/hetida-designer`,
          redirectUrl: window.location.origin,
          clientId: 'hetida-designer',
          responseType: 'code',
          scope: 'openid',
          postLogoutRedirectUri: window.location.origin,
          silentRenew: true,
          silentRenewUrl: `${window.location.origin}/silent-renew.html`,
          logLevel: LogLevel.Warn,
          // TODO take api endpoint from config json
          // TODO also add token to adapter request (which might have totally different URLs)
          secureRoutes: ['/api']
          // autoUserInfo: false,
        };
      })
    )
    .toPromise();

  return new StsConfigHttpLoader(config$);
};

@NgModule({
  imports: [
    AuthModule.forRoot({
      loader: {
        provide: StsConfigLoader,
        useFactory: httpLoaderFactory,
        deps: [HttpClient]
      }
    })
  ],
  exports: [AuthModule]
})
export class AuthHttpConfigModule {}
