import { AbstractBaseItem } from 'src/app/model/base-item';
import { createEntityAdapter, EntityState } from '@ngrx/entity';

export const baseItemEntityAdapter = createEntityAdapter<AbstractBaseItem>();

export interface IBaseItemState extends EntityState<AbstractBaseItem> {}

export const initialBaseItemState: IBaseItemState = baseItemEntityAdapter.getInitialState();
