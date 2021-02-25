import { Injectable } from '@angular/core';
import { ReplaySubject } from 'rxjs';
import { LocalStorageService } from './../local-storage/local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly currentTheme$: ReplaySubject<string> = new ReplaySubject<string>();

  readonly activeTheme: string;

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

  get currentTheme(): ReplaySubject<string> {
    return this.currentTheme$;
  }

  setCurrentTheme(theme: string) {
    this.currentTheme$.next(theme);
  }
}
