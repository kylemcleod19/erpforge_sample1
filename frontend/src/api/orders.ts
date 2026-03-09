import client from "./client";

export interface OrderLineItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name?: string;
  product_sku?: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: number;
  quote_id?: number;
  status: string;
  notes?: string;
  created_at: string;
  line_items: OrderLineItem[];
}

export const ordersApi = {
  list: (status?: string) =>
    client.get<Order[]>("/orders", { params: status ? { status } : {} }).then((r) => r.data),
  get: (id: number) => client.get<Order>(`/orders/${id}`).then((r) => r.data),
  updateStatus: (id: number, status: string) =>
    client.patch<Order>(`/orders/${id}/status`, { status }).then((r) => r.data),
};
