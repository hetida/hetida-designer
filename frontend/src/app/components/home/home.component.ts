import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { AuthService } from './../../auth/auth.service';
import { ContextMenuService } from './../../service/context-menu/context-menu.service';
import { ThemeService } from './../../service/theme/theme.service';

@Component({
  selector: 'hd-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
  constructor(
    private readonly themeService: ThemeService,
    private readonly contextMenuService: ContextMenuService,
    private readonly authService: AuthService
  ) {}

  public get userName$(): Observable<string> {
    return this.authService.userName$();
  }

  public get isAuthenticated$(): Observable<boolean> {
    return this.authService.isAuthenticated$();
  }

  public get isAuthEnabled(): boolean {
    return this.authService.isAuthEnabled();
  }

  public get isLightTheme(): boolean {
    return this.themeService.isLightTheme;
  }

  public get theme(): string {
    return this.themeService.lastTheme;
  }

  public toggleTheme() {
    this.themeService.isLightTheme = !this.themeService.isLightTheme;
    this.themeService.setCurrentTheme(
      this.themeService.isLightTheme ? 'light-theme' : 'dark-theme'
    );
  }

  public logout(): void {
    this.authService.logout();
  }

  public closeContextMenu() {
    this.contextMenuService.disposeAllContextMenus();
  }
}
