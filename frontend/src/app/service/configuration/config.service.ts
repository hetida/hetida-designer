import { HttpClient, HttpContext } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, ReplaySubject } from 'rxjs';
import { Utils } from 'src/app/utils/utils';
import { BYPASS_AUTH } from '../../auth/auth.interceptor';

interface AuthConfig {
  // for more config options see https://github.com/damienbod/angular-auth-oidc-client
  authority: string;
  clientId: string;
  userNameAttribute: string;
}

export interface Configuration {
  readonly apiEndpoint: string;
  authEnabled?: boolean;
  authConfig?: AuthConfig;
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
      .get<Configuration>('assets/hetida_designer_config.json', {
        context: new HttpContext().set(BYPASS_AUTH, true)
      })
      .toPromise();

    // If no authEnabled property is present we will set it to false.
    if (Utils.isNullOrUndefined(this.config.authEnabled)) {
      this.config.authEnabled = false;
    }

    this.config$.next(this.config);
    return this.config;
  }

  public getConfig(): Observable<Configuration> {
    return this.config$.asObservable();
  }
}
