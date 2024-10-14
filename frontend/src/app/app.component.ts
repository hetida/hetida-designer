import { Component, ElementRef, OnInit } from '@angular/core';
import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer } from '@angular/platform-browser';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { ThemeService } from './service/theme/theme.service';
import { OverlayContainer } from '@angular/cdk/overlay';
import { LocalStorageService } from './service/local-storage/local-storage.service';
import { AuthService } from './auth/auth.service';

@Component({
  selector: 'hd-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  constructor(
    private readonly oidcSecurityService: OidcSecurityService,
    private readonly iconRegistry: MatIconRegistry,
    private readonly sanitizer: DomSanitizer,
    private readonly localStorage: LocalStorageService,
    private readonly overlayContainer: OverlayContainer,
    private readonly appElement: ElementRef<Element>,
    private readonly themeService: ThemeService,
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
        .classList.remove(this.themeService.lastTheme);
      this.appElement.nativeElement.classList.remove(
        this.themeService.lastTheme
      );
      this.overlayContainer.getContainerElement().classList.add(theme);
      this.appElement.nativeElement.classList.add(theme);
      this.themeService.lastTheme = theme;
      this.themeService.isLightTheme =
        this.themeService.lastTheme === 'light-theme';
    });

    if (this.authService.isAuthEnabled()) {
      this.oidcSecurityService.checkAuth().subscribe();
    }
  }
}
