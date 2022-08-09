import { Injectable } from '@angular/core';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import { Store } from '@ngrx/store';
import { TransformationState } from '../../store/transformation/transformation.state';
import { setAllTransformations } from '../../store/transformation/transformation.actions';

@Injectable({
  providedIn: 'root'
})
export class TransformationService {
  constructor(
    private readonly store: Store<TransformationState>,
    private readonly httpService: TransformationHttpService
  ) {}

  getTransformations(): void {
    this.httpService.fetchTransformations().subscribe(transformations => {
      this.store.dispatch(setAllTransformations(transformations));
    });
  }
}
