import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, ReplaySubject } from 'rxjs';
import { Utils } from 'src/app/utils/utils';

export interface NewConfiguration {
  authEnabled: boolean;
  authAuthority: string;
  authClientId: string;
  secureRoutes: Array<string>;
  // authLogLevel?
  // authUsernameAttribute?
}

export interface Configuration {
  readonly apiEndpoint: string;
  // TODO is this used in any project?
  readonly forwardAuthHeaders: boolean;
  // TODO rename
  keycloakEnabled?: boolean;
  // TODO add other oauth properties
  readonly keycloakRealm: string;
  readonly keycloakClientId: string;
  readonly keycloakUrl: string;
}

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private readonly config$: ReplaySubject<Configuration> = new ReplaySubject(1);
  config: Configuration;

  constructor(private readonly http: HttpClient) {}

  public async loadConfig(): Promise<Configuration> {
    this.config = await this.http
      .get<Configuration>('assets/hetida_designer_config.json')
      .toPromise();

    // If no keycloakEnabled property is present we will set it to false.
    if (Utils.isNullOrUndefined(this.config.keycloakEnabled)) {
      this.config.keycloakEnabled = false;
    }

    this.config$.next(this.config);
    return this.config;
  }

  public getConfig(): Observable<Configuration> {
    return this.config$.asObservable();
  }
}
