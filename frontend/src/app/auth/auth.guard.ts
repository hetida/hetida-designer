import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  RouterStateSnapshot,
  UrlTree
} from '@angular/router';
import { AutoLoginAllRoutesGuard } from 'angular-auth-oidc-client';
import { Observable } from 'rxjs';
import { ConfigService } from '../service/configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  private authEnabled = false;

  constructor(
    private readonly configService: ConfigService,
    private readonly autoLoginAllRoutesGuard: AutoLoginAllRoutesGuard
  ) {
    this.configService.getConfig().subscribe(config => {
      this.authEnabled = config.authEnabled;
    });
  }

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ):
    | Observable<boolean | UrlTree>
    | Promise<boolean | UrlTree>
    | boolean
    | UrlTree {
    return this.authEnabled
      ? this.autoLoginAllRoutesGuard.canActivate(route, state)
      : true;
  }
}
