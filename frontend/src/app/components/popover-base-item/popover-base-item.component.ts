import { Component, HostBinding, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import {
  createReadOnlyConfig,
  FlowchartConfiguration,
  SVGManipulatorConfiguration
} from 'hetida-flowchart';
import { switchMap } from 'rxjs/operators';
import {
  popoverHeight,
  popoverMinHeight,
  popoverWidth
} from 'src/app/constants/popover-sizes';
import { RevisionState } from 'src/app/enums/revision-state';
import { ShowPopover } from 'src/app/model/show-popover';
import { PopoverService } from 'src/app/service/popover/popover.service';
import { FlowchartConverterService } from 'src/app/service/type-converter/flowchart-converter.service';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { TabItemService } from '../../service/tab-item/tab-item.service';
import { Transformation } from '../../model/transformation';
import { selectTransformationById } from '../../store/transformation/transformation.selectors';

@Component({
  selector: 'hd-popover-base-item',
  templateUrl: './popover-base-item.component.html',
  styleUrls: ['./popover-base-item.component.scss']
})
export class PopoverBaseItemComponent implements OnInit {
  @HostBinding('style.top')
  get topPos(): string {
    if (this.showPopoverData === null) {
      return '0px';
    }
    const bodyRect = window.document.body.getBoundingClientRect();
    if (this.showPopoverData.posY === null) {
      const renderAtY =
        (bodyRect.height -
          (this.showPopoverData.showPreview
            ? popoverHeight
            : popoverMinHeight)) *
        0.5;
      return `${renderAtY}px`;
    }
    const bottomOverflow =
      bodyRect.bottom -
      ((this.showPopoverData.showPreview ? popoverHeight : popoverMinHeight) +
        this.showPopoverData.posY);
    if (bottomOverflow < 0) {
      // would overflow bottom -> Position upwards
      return `${this.showPopoverData.posY + bottomOverflow}px`;
    }
    // normal render
    return `${this.showPopoverData.posY}px`;
  }

  @HostBinding('style.left')
  get leftPos(): string {
    if (this.showPopoverData === null) {
      return '0px';
    }
    let renderAtX: number;
    if (this.showPopoverData.extendRight === false) {
      renderAtX = this.showPopoverData.posX - popoverWidth;
    } else {
      renderAtX = this.showPopoverData.posX;
    }
    return `${renderAtX}px`;
  }

  @HostBinding('style.display')
  get display(): string {
    return this._isPopoverVisible ? 'block' : 'none';
  }

  @HostBinding('style.height')
  get displayHeight(): string {
    if (this.showPopoverData === null) {
      return `${popoverHeight}px`;
    }
    return `${
      this.showPopoverData.showPreview ? popoverHeight : popoverMinHeight
    }px`;
  }

  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly flowchartConverter: FlowchartConverterService,
    private readonly popoverService: PopoverService,
    private readonly tabItemService: TabItemService
  ) {
    this.svgConfiguration = createReadOnlyConfig(
      new SVGManipulatorConfiguration()
    );
    this.svgConfiguration.allowPanning = false;
    this.svgConfiguration.allowZooming = false;
    this.svgConfiguration.showContextMenu = false;
  }

  transformation: Transformation | undefined;

  /**
   * Component Preview Configuration
   */
  componentPreview: FlowchartConfiguration = {
    id: '',
    components: [],
    io: [],
    links: []
  };

  /**
   * Preview SVG Configuration
   */
  public svgConfiguration: SVGManipulatorConfiguration;

  public RevisionState = RevisionState;
  public showPopoverData: ShowPopover | null = null;

  ngOnInit() {
    this.popoverService.onPopover
      .pipe(
        switchMap((showPopoverData: ShowPopover | undefined) => {
          this.showPopoverData = showPopoverData;
          return this.transformationStore.select(
            selectTransformationById(showPopoverData?.itemId)
          );
        })
      )
      .subscribe((transformation: Transformation | undefined) => {
        this.transformation = transformation;
        if (transformation) {
          this._createPreview(transformation);
        }
      });
  }

  get _isPopoverVisible(): boolean {
    return (
      this.transformation !== undefined &&
      this.showPopoverData !== null &&
      this.showPopoverData.visible === true
    );
  }

  close(): void {
    this.popoverService.closePopover();
  }

  open(): void {
    this.tabItemService.addTransformationTab(this.transformation.id);
    this.popoverService.closePopover();
  }

  private _createPreview(transformation: Transformation): void {
    this.componentPreview = this.flowchartConverter.convertComponentToFlowchart(
      transformation
    );
  }

  _dragComponent(event: DragEvent): void {
    event.dataTransfer.effectAllowed = 'all';
    event.dataTransfer.dropEffect = 'none';
    event.dataTransfer.setData(
      'hetida/baseItem',
      JSON.stringify(this.transformation)
    );
  }
}
