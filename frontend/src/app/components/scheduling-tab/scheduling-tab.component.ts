import { ComponentPortal } from '@angular/cdk/portal';
import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { combineLatest, Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { TransformationType } from 'src/app/enums/transformation-type';
import { Transformation } from 'src/app/model/transformation';
import { TransformationActionService } from 'src/app/service/transformation/transformation-action.service';
import { ConfigService } from '../../service/configuration/config.service';
import { ContextMenuService } from 'src/app/service/context-menu/context-menu.service';
import { LocalStorageService } from 'src/app/service/local-storage/local-storage.service';
import { selectHashedTransformationLookupById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { Utils } from 'src/app/utils/utils';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { TransformationContextMenuComponent } from '../transformation-context-menu/transformation-context-menu.component';

@Component({
    selector: 'hd-scheduling-tab',
    templateUrl: './scheduling-tab.component.html',
    styleUrls: ['./scheduling-tab.component.scss'],
})
export class SchedulingTabComponent implements OnInit {
    constructor(
        private readonly localStorageService: LocalStorageService,
        private readonly transformationStore: Store<TransformationState>,
        private readonly transformationActionService: TransformationActionService,
        private readonly tabItemService: TabItemService,
        private readonly contextMenuService: ContextMenuService,
        private readonly httpClient: HttpClient,
        private readonly configService: ConfigService
    ) { }

    public lastOpened: Observable<Transformation[]>;
    public version: string;
    public _userInfoText: string;

    public schedules = [
        { id: 42, name: 53, description: "some job", transformation_id: "abcd1234", transformation_name: "some", transformation_version_tag: "1.0.0", active: true, cron_expression: "*/2 * * * *" },
        { id: 43, name: 54, description: "another job", transformation_id: "abcd1235", transformation_name: "some other", transformation_version_tag: "1.1.0", active: true, cron_expression: "0 8 * * *" }
    ];

    public onDragOver(event: DragEvent): void {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
    }

    public onDrop(event: DragEvent, schedule: any): void {
        event.preventDefault();

        const data = event.dataTransfer.getData('hetida/transformation');
        if (data) {
            try {
                const transformation = JSON.parse(data);
                schedule.transformation_id = transformation.id;
                schedule.transformation_name = transformation.name;
                schedule.transformation_version_tag = transformation.version_tag
            } catch (e) {
                console.error('Failed to parse transformation data', e);
            }
        }
    }

    edit(schedule: any) {
        schedule.original = {
            name: schedule.name,
            cronExpression: schedule.cronExpression
        };
        schedule.editing = true;
    }

    save(schedule: any) {
        schedule.editing = false;

        // TODO: call API here
        console.log('Saved:', schedule);
    }

    cancel(schedule: any) {
        schedule.name = schedule.original.name;
        schedule.cronExpression = schedule.original.cronExpression;
        schedule.editing = false;
    }

    ngOnInit() {
        this.httpClient
            .get<string>('assets/VERSION', { responseType: 'text' as 'json' })
            .subscribe((version: string) => {
                this.version = version;
            });
        this.lastOpened = combineLatest([
            this.localStorageService.notifier,
            this.transformationStore.select(selectHashedTransformationLookupById)
        ]).pipe(
            map(([_, transformationsLookup]) => {
                const lastOpenedTransformationIds: string[] =
                    this.localStorageService.getItem('last-opened') ?? [];

                return lastOpenedTransformationIds
                    .filter(() => !Utils.object.isEmpty(transformationsLookup))
                    .map(transformationId => transformationsLookup[transformationId])
                    .filter((transformation): transformation is Transformation =>
                        Utils.isDefined(transformation)
                    );
            })
        );
        this.configService.getConfig().subscribe(config => {
            this._userInfoText = config.userInfoText;
        });
    }

    get lastOpenedWorkflows() {
        return this.lastOpened.pipe(
            map(transformations => {
                return transformations.filter(
                    transformation => transformation.type === TransformationType.WORKFLOW
                );
            })
        );
    }

    get lastOpenedComponents() {
        return this.lastOpened.pipe(
            map(transformations => {
                return transformations.filter(
                    transformation => transformation.type === TransformationType.COMPONENT
                );
            })
        );
    }

    select(selectedItem: Transformation) {
        this.tabItemService.addTransformationTab(selectedItem.id);
    }

    openTransformationContextMenu(
        selectedItem: Transformation,
        mouseEvent: MouseEvent
    ) {
        const { componentPortalRef } = this.contextMenuService.openContextMenu(
            new ComponentPortal(TransformationContextMenuComponent),
            {
                x: mouseEvent.clientX,
                y: mouseEvent.clientY
            }
        );

        componentPortalRef.instance.transformation = selectedItem;
    }

    newWorkflow(): void {
        this.transformationActionService.newWorkflow();
    }

    newComponent(): void {
        this.transformationActionService.newComponent();
    }
}
