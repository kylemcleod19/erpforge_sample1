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
}

export interface ProductSpec {
  id: number;
  product_id: number;
  label: string;
  url: string;
}

export interface CostNode {
  product_id: number;
  sku: string;
  name: string;
  unit_cost: number;
  rolled_up_cost: number;
  children: CostNode[];
}

export const productsApi = {
  list: () => client.get<Product[]>("/products").then((r) => r.data),
  get: (id: number) => client.get<Product>(`/products/${id}`).then((r) => r.data),
  create: (data: Partial<Product>) => client.post<Product>("/products", data).then((r) => r.data),
  update: (id: number, data: Partial<Product>) =>
    client.put<Product>(`/products/${id}`, data).then((r) => r.data),
  delete: (id: number) => client.delete(`/products/${id}`),

  getBOM: (id: number) => client.get<BOMItem[]>(`/products/${id}/bom`).then((r) => r.data),
  addBOMItem: (id: number, data: { child_product_id: number; quantity: number; unit_of_measure?: string }) =>
    client.post<BOMItem>(`/products/${id}/bom`, data).then((r) => r.data),
  removeBOMItem: (productId: number, bomItemId: number) =>
    client.delete(`/products/${productId}/bom/${bomItemId}`),

  getSpecs: (id: number) => client.get<ProductSpec[]>(`/products/${id}/specs`).then((r) => r.data),
  addSpec: (id: number, data: { label: string; url: string }) =>
    client.post<ProductSpec>(`/products/${id}/specs`, data).then((r) => r.data),
  removeSpec: (productId: number, specId: number) =>
    client.delete(`/products/${productId}/specs/${specId}`),

  getCost: (id: number) => client.get<CostNode>(`/products/${id}/cost`).then((r) => r.data),
};
