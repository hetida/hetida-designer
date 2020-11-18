import { ConfigService } from './../configuration/config.service';
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { Observable } from 'rxjs';
import { AbstractBaseItem } from '../../model/base-item';

@Injectable({
  providedIn: 'root'
})
export class BaseItemHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly http: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public createBaseItem(
    abstractBaseItem: AbstractBaseItem
  ): Observable<AbstractBaseItem> {
    const url = `${this.apiEndpoint}/base-items/`;
    return this.http.post<AbstractBaseItem>(url, abstractBaseItem);
  }

  public getBaseItem(abstractBaseItemId: string): Observable<AbstractBaseItem> {
    const url = `${this.apiEndpoint}/base-items/${abstractBaseItemId}`;
    return this.http.get<AbstractBaseItem>(url);
  }

  public updateBaseItem(
    abstractBaseItem: AbstractBaseItem
  ): Observable<AbstractBaseItem> {
    const url = `${this.apiEndpoint}/base-items/${abstractBaseItem.id}`;
    return this.http.put<AbstractBaseItem>(url, abstractBaseItem);
  }

  public fetchBaseItems(): Observable<Array<AbstractBaseItem>> {
    const url = `${this.apiEndpoint}/base-items/`;
    return this.http.get<Array<AbstractBaseItem>>(url);
  }
}
