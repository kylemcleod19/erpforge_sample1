import client from "./client";

export interface WorkStation {
  id: number;
  name: string;
  description?: string;
  sequence: number;
}

export interface RoutingEntry {
  station_id: number;
  sequence: number;
}

export interface ProductRouting {
  product_id: number;
  routing: RoutingEntry[];
}

export interface WorkOrderLog {
  id: number;
  work_order_id: number;
  station_id: number;
  station_name?: string;
  started_at?: string;
  completed_at?: string;
  notes?: string;
  operator?: string;
}

export interface WorkOrder {
  id: number;
  order_id: number;
  product_id: number;
  product_name?: string;
  product_sku?: string;
  quantity: number;
  status: string;
  current_station_sequence?: number;
  created_at: string;
  logs: WorkOrderLog[];
}

export const manufacturingApi = {
  listStations: () => client.get<WorkStation[]>("/stations").then((r) => r.data),
  createStation: (data: { name: string; description?: string; sequence?: number }) =>
    client.post<WorkStation>("/stations", data).then((r) => r.data),
  updateStation: (id: number, data: Partial<WorkStation>) =>
    client.put<WorkStation>(`/stations/${id}`, data).then((r) => r.data),
  deleteStation: (id: number) => client.delete(`/stations/${id}`),

  getRouting: (productId: number) =>
    client.get<ProductRouting>(`/products/${productId}/routing`).then((r) => r.data),
  setRouting: (productId: number, stationIds: number[]) =>
    client
      .put<ProductRouting>(`/products/${productId}/routing`, { station_ids: stationIds })
      .then((r) => r.data),

  listWorkOrders: (params?: { status?: string; order_id?: number }) =>
    client.get<WorkOrder[]>("/work-orders", { params }).then((r) => r.data),
  getWorkOrder: (id: number) => client.get<WorkOrder>(`/work-orders/${id}`).then((r) => r.data),
  advance: (id: number, data?: { notes?: string; operator?: string }) =>
    client.post<WorkOrder>(`/work-orders/${id}/advance`, data || {}).then((r) => r.data),
  complete: (id: number, data?: { notes?: string; operator?: string }) =>
    client.post<WorkOrder>(`/work-orders/${id}/complete`, data || {}).then((r) => r.data),
};
