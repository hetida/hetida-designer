import { Injectable } from '@angular/core';
import { ReplaySubject } from 'rxjs';
import { LocalStorageService } from '../local-storage/local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  public readonly activeTheme: string;
  public isLightTheme = true;
  public lastTheme = 'light-theme';

  private readonly currentTheme$: ReplaySubject<string> =
    new ReplaySubject<string>();

  constructor(private readonly localStorage: LocalStorageService) {
    let theme: string = this.localStorage.getItem('theme');
    if (theme === null) {
      theme = matchMedia('prefers-color-scheme: dark').matches
        ? 'dark-theme'
        : 'light-theme';
    }
    this.activeTheme = theme;
    this.setCurrentTheme(theme);
  }

  public get currentTheme(): ReplaySubject<string> {
    return this.currentTheme$;
  }

  public setCurrentTheme(theme: string) {
    this.currentTheme$.next(theme);
  }
}
