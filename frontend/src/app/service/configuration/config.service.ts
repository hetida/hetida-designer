import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ReplaySubject } from 'rxjs';
import { Utils } from 'src/app/utils/utils';

export interface Configuration {
  readonly apiEndpoint: string;
  readonly forwardAuthHeaders: boolean;
  keycloakEnabled?: boolean;
  readonly keycloakRealm: string;
  readonly keycloakClientId: string;
  readonly keycloakUrl: string;
}

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private readonly config$: ReplaySubject<Configuration> = new ReplaySubject(1);

  constructor(private readonly http: HttpClient) {}

  public async loadConfig(): Promise<Configuration> {
    const config = await this.http
      .get<Configuration>('assets/hetida_designer_config.json')
      .toPromise();

    // If no keycloakEnabled property is present we will set it to false.
    if (Utils.isNullOrUndefined(config.keycloakEnabled)) {
      config.keycloakEnabled = false;
    }

    this.config$.next(config);
    return config;
  }

  public getConfig(): ReplaySubject<Configuration> {
    return this.config$;
  }
}
