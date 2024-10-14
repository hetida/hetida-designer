import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  UrlTree
} from '@angular/router';
import { AutoLoginPartialRoutesGuard } from 'angular-auth-oidc-client';
import { Observable } from 'rxjs';
import { ConfigService } from '../service/configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard {
  private authEnabled = false;

  constructor(
    private readonly configService: ConfigService,
    private readonly autoLoginPartialRoutesGuard: AutoLoginPartialRoutesGuard
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
      ? this.autoLoginPartialRoutesGuard.canActivate(route, state)
      : true;
  }
}
