import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Documentation } from '../../model/documentation';
import { ConfigService } from './../configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class DocumentationHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly http: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public createDocumentation(
    documentation: Documentation
  ): Observable<Documentation> {
    const url = `${this.apiEndpoint}/documentations/`;
    return this.http.post<Documentation>(url, documentation);
  }

  public getDocumentation(id: string): Observable<Documentation> {
    const url = `${this.apiEndpoint}/documentations/${id}`;
    return this.http.get<Documentation>(url);
  }

  public updateDocumentation(
    documentation: Documentation
  ): Observable<Documentation> {
    const url = `${this.apiEndpoint}/documentations/${documentation.id}`;
    return this.http.put<Documentation>(url, documentation);
  }
}
