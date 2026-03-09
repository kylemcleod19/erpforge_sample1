import client from "./client";

export interface InventoryBalance {
  id: number;
  product_id: number;
  product_name?: string;
  product_sku?: string;
  quantity_on_hand: number;
}

export interface InventoryReservation {
  id: number;
  order_id: number;
  product_id: number;
  product_name?: string;
  quantity_reserved: number;
  created_at: string;
}

export const inventoryApi = {
  listBalances: () => client.get<InventoryBalance[]>("/inventory/balances").then((r) => r.data),
  upsertBalance: (data: { product_id: number; quantity_on_hand: number }) =>
    client.post<InventoryBalance>("/inventory/balances", data).then((r) => r.data),
  listReservations: (orderId?: number) =>
    client
      .get<InventoryReservation[]>("/inventory/reservations", {
        params: orderId ? { order_id: orderId } : {},
      })
      .then((r) => r.data),
};
