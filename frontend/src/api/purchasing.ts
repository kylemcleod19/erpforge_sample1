import client from "./client";

export interface PurchaseRequest {
  id: number;
  order_id: number;
  product_id: number;
  product_name?: string;
  product_sku?: string;
  quantity_needed: number;
  status: string;
  notes?: string;
  created_at: string;
}

export const purchasingApi = {
  list: (status?: string) =>
    client
      .get<PurchaseRequest[]>("/purchasing/requests", { params: status ? { status } : {} })
      .then((r) => r.data),
  updateStatus: (id: number, status: string) =>
    client
      .patch<PurchaseRequest>(`/purchasing/requests/${id}/status`, { status })
      .then((r) => r.data),
};
