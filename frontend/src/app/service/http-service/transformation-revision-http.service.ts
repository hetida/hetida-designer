import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ConfigService } from '../configuration/config.service';
import { Observable } from 'rxjs';
import { TransformationRevision } from '../../model/new-api/transformation-revision';

@Injectable({
  providedIn: 'root'
})
export class TransformationRevisionHttpService {
  private apiEndpoint: string;

  constructor(
    private readonly httpClient: HttpClient,
    private readonly config: ConfigService
  ) {
    this.config.getConfig().subscribe(runtimeConfig => {
      this.apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  public fetchTransformationRevisions(): Observable<
    Array<TransformationRevision>
  > {
    const url = `${this.apiEndpoint}/transformations`;
    return this.httpClient.get<Array<TransformationRevision>>(url);
  }
}
