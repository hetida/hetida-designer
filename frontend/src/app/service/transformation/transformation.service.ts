import { Injectable } from '@angular/core';
import { TransformationHttpService } from '../http-service/transformation-http.service';
import { Store } from '@ngrx/store';
import { TransformationState } from '../../store/transformation/transformation.state';
import {
  removeTransformation,
  setAllTransformations
} from '../../store/transformation/transformation.actions';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { LocalStorageService } from '../local-storage/local-storage.service';

@Injectable({
  providedIn: 'root'
})
export class TransformationService {
  constructor(
    private readonly store: Store<TransformationState>,
    private readonly httpService: TransformationHttpService,
    private readonly localStorageService: LocalStorageService
  ) {}

  getTransformations(): void {
    this.httpService.fetchTransformations().subscribe(transformations => {
      this.store.dispatch(setAllTransformations(transformations));
    });
  }

  deleteTransformation(id: string): Observable<void> {
    return this.httpService.deleteTransformation(id).pipe(
      tap(_ => {
        this.localStorageService.removeItemFromLastOpened(id);
        this.store.dispatch(removeTransformation(id));
      })
    );
  }
}
