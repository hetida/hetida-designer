import { Injectable } from '@angular/core';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { Observable, of } from 'rxjs';
import { first, map } from 'rxjs/operators';
import { ConfigService } from '../service/configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private authEnabled = false;

  constructor(
    private readonly configService: ConfigService,
    private readonly oidcSecurityService: OidcSecurityService
  ) {
    this.configService.getConfig().subscribe(config => {
      this.authEnabled = config.keycloakEnabled;
    });
  }

  /**
   * Returns true once the user is logged in.
   */
  public isAuthenticated$(): Observable<boolean> {
    if (this.authEnabled) {
      return this.oidcSecurityService.isAuthenticated$.pipe(
        map(result => result.isAuthenticated),
        first(authenticated => authenticated === true)
      );
    }
    return of(true);
  }

  public userName$(): Observable<string> {
    if (this.authEnabled) {
      return this.oidcSecurityService.userData$.pipe(
        map(userDataResult => {
          // TODO configurable username attribute?
          return userDataResult.userData?.preferred_username ?? 'no username';
        })
      );
    }
    return of('auth not enabled');
  }

  public logout(): void {
    this.oidcSecurityService.logoff();
  }
}
