import client from "./client";

export interface InvoiceLineItem {
  id: number;
  invoice_id: number;
  product_id?: number;
  description: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Invoice {
  id: number;
  order_id: number;
  shipment_id: number;
  invoice_number: string;
  status: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  created_at: string;
  line_items: InvoiceLineItem[];
}

export const invoicesApi = {
  list: () => client.get<Invoice[]>("/invoices").then((r) => r.data),
  get: (id: number) => client.get<Invoice>(`/invoices/${id}`).then((r) => r.data),
  updateStatus: (id: number, status: string) =>
    client.patch<Invoice>(`/invoices/${id}/status`, { status }).then((r) => r.data),
};
