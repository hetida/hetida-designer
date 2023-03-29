import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

const APP_PREFIX = 'HD-';

@Injectable({
  providedIn: 'root'
})
export class LocalStorageService {
  // only notifies about changes, NOT what has changed
  public readonly notifier: BehaviorSubject<void> = new BehaviorSubject<any>(
    null
  );

  setItem(key: string, value: any) {
    localStorage.setItem(`${APP_PREFIX}${key}`, JSON.stringify(value));
    this.notifier.next(null);
  }

  getItem(key: string) {
    return JSON.parse(localStorage.getItem(`${APP_PREFIX}${key}`));
  }

  removeItem(key: string) {
    localStorage.removeItem(`${APP_PREFIX}${key}`);
    this.notifier.next(null);
  }

  removeItemFromLastOpened(itemId: string) {
    let lastOpened = (this.getItem('last-opened') ?? []) as string[];
    lastOpened = lastOpened.filter(id => id !== itemId);
    this.setItem('last-opened', lastOpened);
  }

  addToLastOpened(itemid: string) {
    let lastOpened = (this.getItem('last-opened') ?? []) as string[];
    // remove any previous occurences of the id
    lastOpened = lastOpened.filter(id => id !== itemid);
    // remove elements while array longer than max. length
    while (lastOpened.length >= 10) {
      lastOpened.pop();
    }
    lastOpened.unshift(itemid);
    this.setItem('last-opened', lastOpened);
  }
}
