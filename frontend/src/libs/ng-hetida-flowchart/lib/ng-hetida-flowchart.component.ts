import {
  AfterViewInit,
  Component,
  ElementRef,
  Input,
  NgZone,
  OnChanges,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import {
  FlowchartComponentConverter,
  FlowchartConfiguration,
  SVGManipulator,
  SVGManipulatorConfiguration
} from 'hetida-flowchart';
import { filter } from 'rxjs/operators';
import { NgHetidaFlowchartService } from './ng-hetida-flowchart.service';

@Component({
  selector: 'hetida-flowchart',
  templateUrl: './ng-hetida-flowchart.component.html',
  styleUrls: ['./ng-hetida-flowchart.component.scss'],
  standalone: false
})
export class NgHetidaFlowchartComponent implements AfterViewInit, OnChanges {
  /**
   * In- and output of the components to be created,
   * emits empty array if all components are created
   */
  @Input() initConfiguration: FlowchartConfiguration | undefined = undefined;

  /**
   * Input for the configuration of the component
   */
  @Input()
  flowchartConfiguration: SVGManipulatorConfiguration =
    new SVGManipulatorConfiguration();

  /**
   * Input for clearing the SVG (except the configured background element)
   */
  @Input() clearSVG = false;

  /**
   * If true, every load will zoom to show entire workflow
   */
  @Input() alwaysShowEntireWorkflow = false;

  /**
   * reference to the svg element
   */
  @ViewChild('svg', { static: true }) svgElement: ElementRef<SVGSVGElement>;

  /**
   * converts FlowchartComponents to SVG Graphics
   */
  private readonly converter: FlowchartComponentConverter =
    new FlowchartComponentConverter();
  /**
   * helper for manipulation the svg and it's elements
   */
  private svgManipulator: SVGManipulator | null = null;

  constructor(
    private readonly ngZone: NgZone,
    private readonly flowchartService: NgHetidaFlowchartService
  ) {}

  ngAfterViewInit() {
    // @Performance: creating the SVGManipulator outside of angular allows for near native performance on the event listeners
    this.ngZone.runOutsideAngular(() =>
      this.createSvgManipulatorWithConfiguration()
    );
    this.checkAndLoadConfiguration(true);
    this.flowchartService.zoomIn$
      .pipe(filter(id => id === this.initConfiguration.id))
      .subscribe(() => this.zoom(true));
    this.flowchartService.zoomOut$
      .pipe(filter(id => id === this.initConfiguration.id))
      .subscribe(() => this.zoom(false));
    this.flowchartService.showEntireWorkflow$
      .pipe(filter(id => id === this.initConfiguration.id))
      .subscribe(() => this.resetView());
  }

  ngOnChanges(changes: SimpleChanges): void {
    this.checkAndLoadConfiguration(
      changes.initConfiguration.previousValue === undefined
    );
    if (
      changes.flowchartConfiguration !== undefined &&
      this.svgManipulator !== null
    ) {
      this.svgManipulator.config = changes.flowchartConfiguration.currentValue;
    }
  }

  private checkAndLoadConfiguration(isInit: boolean): void {
    // don't load if there is no configuration
    if (this.initConfiguration === undefined || this.svgManipulator === null) {
      return;
    }
    this.converter.loadFromConfiguration(
      this.initConfiguration,
      this.svgManipulator,
      this.clearSVG,
      isInit || this.alwaysShowEntireWorkflow
    );
  }

  /**
   * passes the configuration from the component into the svg manipulator
   */
  private createSvgManipulatorWithConfiguration() {
    this.flowchartConfiguration.backgroundElementId = 'flowchart-grid-element';
    this.svgManipulator = new SVGManipulator(
      this.svgElement.nativeElement,
      this.flowchartConfiguration
    );
  }

  private zoom(zoomIn: boolean): void {
    this.svgManipulator.zoomViewBox(zoomIn);
  }

  private resetView(): void {
    this.svgManipulator.showEntireWorkflow();
  }
}
