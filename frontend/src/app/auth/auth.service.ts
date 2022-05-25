import { Injectable } from '@angular/core';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { Observable } from 'rxjs';
import { first, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  constructor(private readonly oidcSecurityService: OidcSecurityService) {}

  /**
   * Returns true once the user is logged in.
   */
  public isAuthenticated$(): Observable<boolean> {
    return this.oidcSecurityService.isAuthenticated$.pipe(
      map(result => result.isAuthenticated),
      first(authenticated => authenticated === true)
    );
  }
}
