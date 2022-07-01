import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { mergeMap } from 'rxjs/operators';
import { AuthService } from '../auth.service';
import { ConfigService } from '../configuration/config.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private forwardAuthHeaders: boolean;
  private keycloakEnabled: boolean;

  constructor(
    private readonly config: ConfigService,
    private readonly auth: AuthService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.forwardAuthHeaders = runtimeConfig.forwardAuthHeaders;
      this.keycloakEnabled = runtimeConfig.keycloakEnabled;
    });
  }

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    if (this.keycloakEnabled === false) {
      return next.handle(request);
    }

    if (request.url.includes('asset')) {
      return next.handle(request);
    }

    return this.auth.getToken().pipe(
      mergeMap(token => {
        const requestWithToken = request.clone({
          withCredentials: this.forwardAuthHeaders ? true : false,
          setHeaders: {
            Authorization: `Bearer ${token}`
          }
        });
        return next.handle(requestWithToken);
      })
    );
  }
}
