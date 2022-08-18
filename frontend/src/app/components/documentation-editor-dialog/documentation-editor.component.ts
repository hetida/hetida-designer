import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Input,
  OnInit,
  ViewChild
} from '@angular/core';
import { SafeHtml } from '@angular/platform-browser';
import { Store } from '@ngrx/store';
import { first } from 'rxjs/operators';
import { BaseItemService } from 'src/app/service/base-item/base-item.service';
import { selectTransformationById } from 'src/app/store/transformation/transformation.selectors';
import { TransformationState } from 'src/app/store/transformation/transformation.state';
import { Utils } from 'src/app/utils/utils';
import { MarkdownService } from '../../service/documentation/markdown.service';

const INITIAL_DOCUMENTATION_TEMPLATE = `
# New Component/Workflow
## Description
## Inputs
## Outputs
## Details
## Examples
`;

@Component({
  selector: 'hd-documentation-editor',
  templateUrl: './documentation-editor.component.html',
  styleUrls: ['./documentation-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DocumentationEditorComponent implements OnInit {
  public markdown = '';
  public parsedMarkdown: SafeHtml;

  @Input() itemId: string;
  @Input() editMode = false;

  @ViewChild('editorRef') editorRef: ElementRef;
  @ViewChild('previewRef') previewRef: ElementRef;

  constructor(
    private readonly transformationStore: Store<TransformationState>,
    private readonly baseItemService: BaseItemService,
    private readonly markdownService: MarkdownService,
    private readonly changeDetection: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.transformationStore
      .select(selectTransformationById(this.itemId))
      .pipe(first())
      .subscribe(transformation => {
        if (Utils.isNullOrUndefined(transformation.documentation)) {
          this.markdown = INITIAL_DOCUMENTATION_TEMPLATE;
          this.parsedMarkdown = this.markdownService.parseMarkdown(
            this.markdown
          );
          this.changeDetection.detectChanges();
          return;
        }
        this.markdown = transformation.documentation;
        this.parsedMarkdown = this.markdownService.parseMarkdown(this.markdown);
        this.changeDetection.detectChanges();
      });
  }

  public parseMarkdown(rawMarkdown: string) {
    this.parsedMarkdown = this.markdownService.parseMarkdown(rawMarkdown);
    this.markdown = rawMarkdown;
    this.changeDetection.detectChanges();
  }

  public switchEdit(): void {
    this.editMode = !this.editMode;

    this.transformationStore
      .select(selectTransformationById(this.itemId))
      .pipe(first())
      .subscribe(transformation =>
        this.baseItemService.updateTransformation({
          ...transformation,
          documentation: this.markdown
        })
      );
  }

  /**
   *
   * On editor scroll, scrolls the markdown preview proportionally.
   *
   * @param event Scroll event
   */
  public editorRefScroll(event: Event) {
    const editor = event.currentTarget as HTMLDivElement;
    const preview = this.previewRef.nativeElement as HTMLTextAreaElement;

    const scrollPercentageOfEditor =
      (100 / (editor.scrollHeight - editor.clientHeight)) * editor.scrollTop;
    const scrollProportional =
      (preview.scrollHeight - preview.clientHeight) *
      (scrollPercentageOfEditor / 100);

    preview.scroll({ top: scrollProportional });
  }
}
