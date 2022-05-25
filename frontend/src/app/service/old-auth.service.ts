import { Injectable, NgZone } from '@angular/core';
import { Observable, Observer } from 'rxjs';
import * as Cloak from 'src/app/keycloak/keycloak';
import { Configuration } from './configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class OldAuthService {
  constructor(private readonly zone: NgZone) {}

  private static config: Cloak.KeycloakConfig;

  static keycloak: Cloak.KeycloakInstance;

  static init(
    config: Configuration
  ): Cloak.KeycloakPromise<boolean, Cloak.KeycloakError> {
    OldAuthService.config = {
      realm: config.keycloakRealm,
      url: config.keycloakUrl,
      clientId: config.keycloakClientId
    };

    OldAuthService.keycloak = Cloak(OldAuthService.config);

    return OldAuthService.keycloak.init({ onLoad: 'login-required' });
  }

  static isAuthenticated(): boolean {
    return !!OldAuthService.keycloak.authenticated;
  }

  /**
   * Get user roles if available otherwise returns empty Array
   */
  static getUserRoles(): string[] {
    if (OldAuthService.keycloak.realmAccess) {
      return OldAuthService.keycloak.realmAccess.roles;
    }

    return [];
  }

  static hasRoles(roles: string[]): boolean {
    return roles.every(role => OldAuthService.hasRole(role));
  }

  static hasRole(role: string): boolean {
    return OldAuthService.getUserRoles().includes(role);
  }

  static hasOneOfRoles(roles: string[]): boolean {
    return (
      OldAuthService.getUserRoles().filter(x => roles.includes(x)).length > 0
    );
  }

  // TODO display name for new oauth
  static getFullName(): string {
    const keycloak = OldAuthService.keycloak;
    if (keycloak && keycloak.tokenParsed) {
      return keycloak.tokenParsed.name;
    }

    return 'no keycloak';
  }

  static logout(): void {
    OldAuthService.keycloak.logout();
  }

  getToken(): Observable<string> {
    return new Observable((observer: Observer<string>) => {
      if (
        OldAuthService.keycloak.token !== null &&
        OldAuthService.keycloak.token !== undefined
      ) {
        OldAuthService.keycloak
          .updateToken(900)
          .then(() => {
            this.zone.run(() => {
              if (
                OldAuthService.keycloak.token !== null ||
                OldAuthService.keycloak.token !== undefined
              ) {
                observer.next(OldAuthService.keycloak.token);
              }

              observer.complete();
            });
          })
          .catch(() => {
            OldAuthService.logout();
          });
      } else {
        OldAuthService.logout();
      }
    });
  }
}
