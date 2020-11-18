import { Injectable, NgZone } from '@angular/core';
import { Observable, Observer } from 'rxjs';
import * as Cloak from 'src/app/keycloak/keycloak';
import { Configuration } from './configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  constructor(private readonly zone: NgZone) {}
  private static config: Cloak.KeycloakConfig;

  static keycloak: Cloak.KeycloakInstance;

  static init(
    config: Configuration
  ): Cloak.KeycloakPromise<boolean, Cloak.KeycloakError> {
    AuthService.config = {
      realm: config.keycloakRealm,
      url: config.keycloakUrl,
      clientId: config.keycloakClientId
    };

    AuthService.keycloak = Cloak(AuthService.config);

    return AuthService.keycloak.init({ onLoad: 'login-required' });
  }

  static isAuthenticated(): boolean {
    return !!AuthService.keycloak.authenticated;
  }

  /**
   * Get user roles if available otherwise returns empty Array
   */
  static getUserRoles(): string[] {
    if (AuthService.keycloak.realmAccess) {
      return AuthService.keycloak.realmAccess.roles;
    }

    return [];
  }

  static hasRoles(roles: string[]): boolean {
    return roles.every(role => AuthService.hasRole(role));
  }

  static hasRole(role: string): boolean {
    return AuthService.getUserRoles().includes(role);
  }

  static hasOneOfRoles(roles: string[]): boolean {
    return AuthService.getUserRoles().filter(x => roles.includes(x)).length > 0;
  }

  static getFullName(): string {
    const keycloak = AuthService.keycloak;
    if (keycloak && keycloak.tokenParsed) {
      return keycloak.tokenParsed.name;
    }

    return 'no keycloak';
  }

  static logout(): void {
    AuthService.keycloak.logout();
  }

  getToken(): Observable<string> {
    return new Observable((observer: Observer<string>) => {
      if (
        AuthService.keycloak.token !== null &&
        AuthService.keycloak.token !== undefined
      ) {
        AuthService.keycloak
          .updateToken(900)
          .then(() => {
            this.zone.run(() => {
              if (
                AuthService.keycloak.token !== null ||
                AuthService.keycloak.token !== undefined
              ) {
                observer.next(AuthService.keycloak.token);
              }

              observer.complete();
            });
          })
          .catch(() => {
            AuthService.logout();
          });
      } else {
        AuthService.logout();
      }
    });
  }
}
