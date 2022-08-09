export enum TabItemType {
  BASE_ITEM = 'BASE_ITEM',
  DOCUMENTATION = 'DOCUMENTATION'
}

export interface TabItem {
  id: string; // A hash identifying the tab item: 'transformationId-tabItemType'.
  transformationId: string;
  tabItemType: TabItemType;
  initialDocumentationEditMode?: boolean;
}
