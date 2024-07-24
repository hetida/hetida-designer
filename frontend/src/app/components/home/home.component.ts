import { Component, ElementRef, OnInit } from '@angular/core';
import { OverlayContainer } from '@angular/cdk/overlay';
import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer } from '@angular/platform-browser';
import { Observable } from 'rxjs';
import { AuthService } from './../../auth/auth.service';
import { ContextMenuService } from './../../service/context-menu/context-menu.service';
import { LocalStorageService } from './../../service/local-storage/local-storage.service';
import { ThemeService } from './../../service/theme/theme.service';

@Component({
  selector: 'hd-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  private lastTheme = 'light-theme';

  public lightTheme = true;

  constructor(
    private readonly iconRegistry: MatIconRegistry,
    private readonly sanitizer: DomSanitizer,
    private readonly localStorage: LocalStorageService,
    private readonly overlayContainer: OverlayContainer,
    private readonly themeService: ThemeService,
    private readonly appElement: ElementRef<Element>,
    private readonly contextMenuService: ContextMenuService,
    private readonly authService: AuthService
  ) {
    this.iconRegistry.addSvgIcon(
      'icon-component',
      this.sanitizer.bypassSecurityTrustResourceUrl('assets/svg/component.svg')
    );

    this.iconRegistry.addSvgIcon(
      'icon-workflow',
      this.sanitizer.bypassSecurityTrustResourceUrl('assets/svg/workflow.svg')
    );
    this.iconRegistry.addSvgIcon(
      'icon-published-workflow',
      this.sanitizer.bypassSecurityTrustResourceUrl(
        'assets/svg/published_workflow.svg'
      )
    );
    this.iconRegistry.addSvgIcon(
      'icon-published-component',
      this.sanitizer.bypassSecurityTrustResourceUrl(
        'assets/svg/published_component.svg'
      )
    );
  }

  ngOnInit() {
    this.themeService.currentTheme.subscribe(theme => {
      this.localStorage.setItem('theme', theme);
      this.overlayContainer
        .getContainerElement()
        .classList.remove(this.lastTheme);
      this.appElement.nativeElement.classList.remove(this.lastTheme);
      this.overlayContainer.getContainerElement().classList.add(theme);
      this.appElement.nativeElement.classList.add(theme);
      this.lastTheme = theme;
      this.lightTheme = this.lastTheme === 'light-theme';
    });
  }

  public toggleTheme() {
    this.lightTheme = !this.lightTheme;
    this.themeService.setCurrentTheme(
      this.lightTheme ? 'light-theme' : 'dark-theme'
    );
  }

  public get theme(): string {
    return this.lastTheme;
  }

  public get userName$(): Observable<string> {
    return this.authService.userName$();
  }

  public get isAuthenticated$(): Observable<boolean> {
    return this.authService.isAuthenticated$();
  }

  public logout(): void {
    this.authService.logout();
  }

  public closeContextMenu() {
    this.contextMenuService.disposeAllContextMenus();
  }
}
