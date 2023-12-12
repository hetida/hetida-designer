import {
  HttpContextToken,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable, Injector } from '@angular/core';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { Observable } from 'rxjs';
import { ConfigService } from '../service/configuration/config.service';
import { Utils } from '../utils/utils';

export const BYPASS_AUTH = new HttpContextToken(() => false);

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private authEnabled = false;
  private oidcSecurityService: OidcSecurityService;

  constructor(
    private readonly configService: ConfigService,
    private readonly injector: Injector
  ) {
    this.configService.getConfig().subscribe(config => {
      this.authEnabled = config.authEnabled;
    });
  }

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler
  ): Observable<HttpEvent<unknown>> {
    if (this.authEnabled || !request.context.get(BYPASS_AUTH)) {
      if (!Utils.isDefined(this.oidcSecurityService)) {
        this.oidcSecurityService = this.injector.get(OidcSecurityService);
      }

      this.oidcSecurityService.getAccessToken().subscribe(token => {
        if (Utils.isDefined(token)) {
          request = request.clone({
            headers: request.headers.set('Authorization', `Bearer ${token}`)
          });
        }
      });
    }
    return next.handle(request);
  }
}
