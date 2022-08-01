import { Injectable } from '@angular/core';
import { TransformationRevisionHttpService } from '../http-service/transformation-revision-http.service';
import { Store } from '@ngrx/store';
import { TransformationRevisionState } from '../../store/transformation-revision/transformation-revision.state';
import { setAllTransformationRevisions } from '../../store/transformation-revision/transformation-revision.actions';

@Injectable({
  providedIn: 'root'
})
export class TransformationRevisionService {
  constructor(
    private readonly store: Store<TransformationRevisionState>,
    private readonly httpService: TransformationRevisionHttpService
  ) {}

  getTransformationRevisions(): void {
    this.httpService
      .fetchTransformationRevisions()
      .subscribe(transformationRevisions => {
        console.log(transformationRevisions);
        this.store.dispatch(
          setAllTransformationRevisions(transformationRevisions)
        );
      });
  }
}
