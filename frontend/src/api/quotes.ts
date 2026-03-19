import client from "./client";

export interface QuoteLineItem {
  id: number;
  quote_id: number;
  product_id: number;
  product_name?: string;
  product_sku?: string;
  quantity: number;
  unit_price: number;
  lead_time_days?: number;
  subtotal: number;
}

export interface Quote {
  id: number;
  customer_name: string;
  customer_email?: string;
  status: string;
  expires_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  line_items: QuoteLineItem[];
}

export const quotesApi = {
  list: (status?: string) =>
    client.get<Quote[]>("/quotes", { params: status ? { status } : {} }).then((r) => r.data),
  get: (id: number) => client.get<Quote>(`/quotes/${id}`).then((r) => r.data),
  create: (data: { customer_name: string; customer_email?: string; notes?: string }) =>
    client.post<Quote>("/quotes", data).then((r) => r.data),
  update: (id: number, data: Partial<Quote>) =>
    client.put<Quote>(`/quotes/${id}`, data).then((r) => r.data),

  addLineItem: (
    id: number,
    data: { product_id: number; quantity: number; unit_price: number; lead_time_days?: number }
  ) => client.post<QuoteLineItem>(`/quotes/${id}/line-items`, data).then((r) => r.data),
  removeLineItem: (quoteId: number, itemId: number) =>
    client.delete(`/quotes/${quoteId}/line-items/${itemId}`),

  transition: (id: number, status: string) =>
    client.post<Quote>(`/quotes/${id}/status`, { status }).then((r) => r.data),
  convert: (id: number, turnstileToken?: string) =>
    client
      .post(`/quotes/${id}/convert`, undefined, turnstileToken ? { headers: { "CF-Turnstile-Response": turnstileToken } } : {})
      .then((r) => r.data),
};
