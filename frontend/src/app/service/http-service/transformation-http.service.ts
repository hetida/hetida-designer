import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../configuration/config.service';
import { Observable } from 'rxjs';
import { Transformation } from '../../model/new-api/transformation';

@Injectable({
  providedIn: 'root'
})
export class TransformationHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly httpClient: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public fetchTransformations(): Observable<Array<Transformation>> {
    const url = `${this.apiEndpoint}/transformations`;
    return this.httpClient.get<Array<Transformation>>(url);
  }
}
