import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Adapter, TestWiring } from 'hd-wiring';
import { Observable } from 'rxjs';
import { ConfigService } from '../configuration/config.service';

@Injectable({
  providedIn: 'root'
})
export class WiringHttpService {
  private _apiEndpoint: string;

  constructor(
    private readonly _http: HttpClient,
    private readonly _config: ConfigService
  ) {
    this._config.getConfig().subscribe(runtimeConfig => {
      this._apiEndpoint = runtimeConfig.apiEndpoint;
    });
  }

  saveWiring(workflowWiring: TestWiring): Observable<TestWiring> {
    return this._http.post<TestWiring>(
      `${this._apiEndpoint}/wirings`,
      workflowWiring
    );
  }

  updateWiring(workflowWiring: TestWiring): Observable<TestWiring> {
    return this._http.put<TestWiring>(
      `${this._apiEndpoint}/wirings/${workflowWiring}`, // id
      workflowWiring
    );
  }

  getAdapterList(): Observable<Adapter[]> {
    const url = `${this._apiEndpoint}/adapters/`;
    return this._http.get<Adapter[]>(url);
  }
}
