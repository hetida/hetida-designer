import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Inject,
  Input,
  OnInit,
  ViewChild
} from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { SafeHtml } from '@angular/platform-browser';
import { first } from 'rxjs/operators';
import { DocumentationService } from 'src/app/service/documentation/documentation.service';
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
  selector: 'hd-documentation-editor-dialog',
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
    public dialogRef: MatDialogRef<DocumentationEditorComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { id: string },
    private readonly documentationService: DocumentationService,
    private readonly markdownService: MarkdownService,
    private readonly changeDetection: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.documentationService
      .getDocumentation(this.data.id ?? this.itemId)
      .pipe(first())
      .subscribe(doc => {
        if (Utils.isNullOrUndefined(doc.document)) {
          this.markdown = INITIAL_DOCUMENTATION_TEMPLATE;
          this.parsedMarkdown = this.markdownService.parseMarkdown(
            this.markdown
          );
          this.changeDetection.detectChanges();
          return;
        }
        this.markdown = doc.document;
        this.parsedMarkdown = this.markdownService.parseMarkdown(this.markdown);
        this.changeDetection.detectChanges();
      });
  }

  public parseMarkdown(rawMarkdown: string) {
    this.parsedMarkdown = this.markdownService.parseMarkdown(rawMarkdown);
    this.markdown = rawMarkdown;
    this.changeDetection.detectChanges();
  }

  public onClose(): void {
    this.dialogRef.close();
  }

  public switchEdit(): void {
    this.editMode = !this.editMode;
    this.documentationService
      .updateDocumentation({
        id: this.data.id ?? this.itemId,
        document: this.markdown
      })
      .subscribe();
  }

  /**
   *
   * On editor scroll, scrolls the markdown preview proprional.
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
