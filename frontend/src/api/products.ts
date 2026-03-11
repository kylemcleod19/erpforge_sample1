import client from "./client";

export interface Product {
  id: number;
  sku: string;
  name: string;
  description?: string;
  unit_price: number;
  unit_cost: number;
  unit_of_measure: string;
  created_at: string;
  // Phase 1 enrichment
  category?: string;
  revision: number;
  lifecycle_status: string;
  item_type: string;
  traceability_type: string;
  compliance_required: boolean;
  bom_items: BOMItem[];
  specs: ProductSpec[];
}

export interface BOMItem {
  id: number;
  parent_product_id: number;
  child_product_id: number;
  child_product_name?: string;
  child_product_sku?: string;
  quantity: number;
  unit_of_measure: string;
  bom_revision_id?: number;
  // Phase 3 enrichment
  reference_designator?: string;
  component_type?: string;
  notes?: string;
  line_designator?: string;
  warnings?: string[];
}

export interface BOMItemAlternate {
  id: number;
  bom_item_id: number;
  alternate_product_id: number;
  alternate_product_name?: string;
  alternate_product_sku?: string;
  priority: number;
  notes?: string;
}

export interface BOMRevision {
  id: number;
  product_id: number;
  revision_number: number;
  status: string;
  notes?: string;
  created_at: string;
  approved_by?: string;
  approved_at?: string;
}

export interface ProductSpec {
  id: number;
  product_id: number;
  label: string;
  url: string;
}

export interface ProductCompliance {
  id: number;
  product_id: number;
  scope: string;
  cert_type: string;
  cert_number?: string;
  issued_date?: string;
  expiry_date?: string;
  document_url?: string;
  notes?: string;
  created_at: string;
}

export interface CostNode {
  product_id: number;
  sku: string;
  name: string;
  unit_cost: number;
  rolled_up_cost: number;
  children: CostNode[];
}

// BOM CSV Import types

export interface ColumnMapping {
  csv_column: string;
  mapped_to: string | null;
}

export interface ColumnDetectResponse {
  csv_columns: string[];
  suggested_mappings: ColumnMapping[];
  available_fields: { field: string; description: string; required: boolean }[];
  sample_rows: Record<string, string>[];
}

export interface BOMImportRow {
  parent_sku: string;
  child_sku: string;
  quantity: number;
  ref_designator?: string;
  line_designator?: string;
  unit_of_measure?: string;
  component_type?: string;
  notes?: string;
  row_number?: number;
  row_errors?: string[];
  parent_product_id?: number;
  child_product_id?: number;
}

export interface BOMConflict {
  parent_sku: string;
  parent_product_id: number;
  child_sku: string;
  child_product_id: number;
  existing_quantity: number;
  existing_ref_designator?: string;
  new_quantity: number;
  new_ref_designator?: string;
  existing_line_designator?: string;
  new_line_designator?: string;
  existing_unit_of_measure?: string;
  new_unit_of_measure?: string;
  existing_component_type?: string;
  new_component_type?: string;
  existing_notes?: string;
  new_notes?: string;
}

export interface BOMImportPreviewResponse {
  new_rows: BOMImportRow[];
  conflicts: BOMConflict[];
  errors: string[];
  column_mappings?: ColumnMapping[];
}

export interface BOMImportApplyResponse {
  created: number;
  updated: number;
  skipped: number;
}

export const productsApi = {
  list: (itemTypes?: string[]) => {
    const params = itemTypes?.length
      ? new URLSearchParams(itemTypes.map((t) => ["item_type", t]))
      : undefined;
    return client.get<Product[]>("/products", { params }).then((r) => r.data);
  },
  get: (id: number) => client.get<Product>(`/products/${id}`).then((r) => r.data),
  create: (data: Partial<Product>) => client.post<Product>("/products", data).then((r) => r.data),
  update: (id: number, data: Partial<Product>) =>
    client.put<Product>(`/products/${id}`, data).then((r) => r.data),
  delete: (id: number) => client.delete(`/products/${id}`),

  getBOM: (id: number) => client.get<BOMItem[]>(`/products/${id}/bom`).then((r) => r.data),
  addBOMItem: (
    id: number,
    data: {
      child_product_id: number;
      quantity: number;
      unit_of_measure?: string;
      reference_designator?: string;
      component_type?: string;
      notes?: string;
      line_designator?: string;
    },
    revisionId?: number,
  ) =>
    client
      .post<BOMItem>(`/products/${id}/bom`, data, {
        params: revisionId ? { revision_id: revisionId } : undefined,
      })
      .then((r) => r.data),
  removeBOMItem: (productId: number, bomItemId: number) =>
    client.delete(`/products/${productId}/bom/${bomItemId}`),

  listAlternates: (productId: number, bomItemId: number) =>
    client
      .get<BOMItemAlternate[]>(`/products/${productId}/bom/${bomItemId}/alternates`)
      .then((r) => r.data),
  addAlternate: (
    productId: number,
    bomItemId: number,
    data: { alternate_product_id: number; priority?: number; notes?: string },
  ) =>
    client
      .post<BOMItemAlternate>(`/products/${productId}/bom/${bomItemId}/alternates`, data)
      .then((r) => r.data),
  removeAlternate: (productId: number, bomItemId: number, altId: number) =>
    client.delete(`/products/${productId}/bom/${bomItemId}/alternates/${altId}`),

  listRevisions: (productId: number) =>
    client.get<BOMRevision[]>(`/products/${productId}/bom-revisions`).then((r) => r.data),
  createRevision: (productId: number, data: { revision_number: number; notes?: string }) =>
    client
      .post<BOMRevision>(`/products/${productId}/bom-revisions`, data)
      .then((r) => r.data),
  approveRevision: (productId: number, revId: number, approvedBy: string) =>
    client
      .patch<BOMRevision>(`/products/${productId}/bom-revisions/${revId}/approve`, {
        approved_by: approvedBy,
      })
      .then((r) => r.data),
  getBOMForRevision: (productId: number, revId: number) =>
    client
      .get<BOMItem[]>(`/products/${productId}/bom-revisions/${revId}/bom`)
      .then((r) => r.data),

  getSpecs: (id: number) => client.get<ProductSpec[]>(`/products/${id}/specs`).then((r) => r.data),
  addSpec: (id: number, data: { label: string; url: string }) =>
    client.post<ProductSpec>(`/products/${id}/specs`, data).then((r) => r.data),
  removeSpec: (productId: number, specId: number) =>
    client.delete(`/products/${productId}/specs/${specId}`),

  listCompliance: (id: number) =>
    client.get<ProductCompliance[]>(`/products/${id}/compliance`).then((r) => r.data),
  addCompliance: (id: number, data: Partial<ProductCompliance>) =>
    client.post<ProductCompliance>(`/products/${id}/compliance`, data).then((r) => r.data),
  removeCompliance: (productId: number, certId: number) =>
    client.delete(`/products/${productId}/compliance/${certId}`),

  getCost: (id: number) => client.get<CostNode>(`/products/${id}/cost`).then((r) => r.data),

  // BOM CSV Import — three-step flow
  bomDetectColumns: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return client
      .post<ColumnDetectResponse>("/products/bom/import/detect-columns", fd)
      .then((r) => r.data);
  },

  bomImportPreview: (file: File, columnMappings?: Record<string, string>) => {
    const fd = new FormData();
    fd.append("file", file);
    if (columnMappings) {
      fd.append("column_mappings", JSON.stringify(columnMappings));
    }
    return client
      .post<BOMImportPreviewResponse>("/products/bom/import/preview", fd)
      .then((r) => r.data);
  },

  bomImportApply: (rows: BOMImportRow[], upsertPairs: [string, string][]) =>
    client
      .post<BOMImportApplyResponse>("/products/bom/import/apply", { rows, upsert_pairs: upsertPairs })
      .then((r) => r.data),

  bomImportTemplate: (type: "pcba" | "mechanical") => {
    // Trigger download via window
    const url = `/api/products/bom/import/template?type=${type}`;
    const a = document.createElement("a");
    a.href = url;
    a.download = `bom_template_${type}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },
};
