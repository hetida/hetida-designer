import { Injectable } from '@angular/core';
import { LocalStorageService } from './../local-storage/local-storage.service';
import { ReplaySubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly currentTheme$: ReplaySubject<string> = new ReplaySubject<
    string
  >();

  constructor(private readonly localStorgage: LocalStorageService) {
    let theme: string = this.localStorgage.getItem('theme');
    if (theme === null) {
      theme = matchMedia('prefers-color-scheme: dark').matches
        ? 'dark-theme'
        : 'light-theme';
    }
    this.setCurrentTheme(theme);
  }

  public get currentTheme(): ReplaySubject<string> {
    return this.currentTheme$;
  }

  public setCurrentTheme(theme: string) {
    this.currentTheme$.next(theme);
  }
}
