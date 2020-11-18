import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { DocumentationHttpService } from './../http-service/documentation-http.service';
import { Documentation } from '../../model/documentation';

@Injectable({
  providedIn: 'root'
})
export class DocumentationService {
  constructor(
    private readonly documentationHttpService: DocumentationHttpService
  ) {}

  public getDocumentation(id: string): Observable<Documentation> {
    return this.documentationHttpService.getDocumentation(id);
  }

  public updateDocumentation(documentation: Documentation) {
    return this.documentationHttpService.updateDocumentation(documentation);
  }

  public createDocumentation(documentation: Documentation) {
    return this.documentationHttpService.createDocumentation(documentation);
  }
}
