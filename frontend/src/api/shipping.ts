import client from "./client";

export interface Shipment {
  id: number;
  order_id: number;
  shipping_account_number?: string;
  carrier?: string;
  tracking_number?: string;
  shipped_at?: string;
  notes?: string;
}

export const shippingApi = {
  list: () => client.get<Shipment[]>("/shipments").then((r) => r.data),
  get: (id: number) => client.get<Shipment>(`/shipments/${id}`).then((r) => r.data),
  create: (data: Partial<Shipment>, turnstileToken?: string) =>
    client
      .post<Shipment>("/shipments", data, turnstileToken ? { headers: { "CF-Turnstile-Response": turnstileToken } } : {})
      .then((r) => r.data),
};
