import {
  Button, Card, Descriptions, Select, Space, Table, Tag, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { inventoryApi, InventoryReservation } from "../api/inventory";
import { manufacturingApi, WorkOrder } from "../api/manufacturing";
import { Order, ordersApi } from "../api/orders";

const { Title } = Typography;

const ORDER_STATUS_COLOR: Record<string, string> = {
  pending: "blue", in_progress: "processing", shipped: "cyan",
  invoiced: "green", cancelled: "red",
};

const WO_STATUS_COLOR: Record<string, string> = {
  queued: "default", in_progress: "processing", completed: "success",
};

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>();
  const oid = parseInt(id!);

  const [order, setOrder] = useState<Order | null>(null);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [reservations, setReservations] = useState<InventoryReservation[]>([]);
  const [newStatus, setNewStatus] = useState<string>("");

  const load = async () => {
    const [o, wos, res] = await Promise.all([
      ordersApi.get(oid),
      manufacturingApi.listWorkOrders({ order_id: oid }),
      inventoryApi.listReservations(oid),
    ]);
    setOrder(o);
    setWorkOrders(wos);
    setReservations(res);
  };

  useEffect(() => { load(); }, [oid]);

  const updateStatus = async () => {
    if (!newStatus) return;
    try { await ordersApi.updateStatus(oid, newStatus); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const advance = async (woId: number) => {
    try { await manufacturingApi.advance(woId); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const complete = async (woId: number) => {
    try { await manufacturingApi.complete(woId); load(); }
    catch (e: any) { message.error(e.message); }
  };

  if (!order) return <div>Loading...</div>;

  return (
    <div>
      <Title level={3}>Order #{order.id}</Title>

      <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="Quote">{order.quote_id ? `#${order.quote_id}` : "—"}</Descriptions.Item>
        <Descriptions.Item label="Status">
          <Tag color={ORDER_STATUS_COLOR[order.status]}>{order.status.toUpperCase()}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Created">{new Date(order.created_at).toLocaleString()}</Descriptions.Item>
        <Descriptions.Item label="Update Status">
          <Space>
            <Select style={{ width: 160 }} placeholder="New status"
              value={newStatus || undefined}
              onChange={setNewStatus}
              options={["pending", "in_progress", "shipped", "invoiced", "cancelled"].map((s) => ({ value: s, label: s }))}
            />
            <Button type="primary" onClick={updateStatus}>Update</Button>
          </Space>
        </Descriptions.Item>
      </Descriptions>

      <Card title="Line Items" style={{ marginBottom: 24 }}>
        <Table
          rowKey="id" size="small"
          dataSource={order.line_items}
          columns={[
            { title: "SKU", dataIndex: "product_sku", key: "sku" },
            { title: "Product", dataIndex: "product_name", key: "name" },
            { title: "Qty", dataIndex: "quantity", key: "qty" },
            { title: "Unit Price", dataIndex: "unit_price", key: "price", render: (v: number) => `$${Number(v).toFixed(2)}` },
          ]}
        />
      </Card>

      <Card title="Work Orders" style={{ marginBottom: 24 }}>
        <Table
          rowKey="id" size="small"
          dataSource={workOrders}
          columns={[
            { title: "ID", dataIndex: "id", key: "id" },
            { title: "Product", dataIndex: "product_name", key: "product" },
            { title: "Qty", dataIndex: "quantity", key: "qty" },
            {
              title: "Status", dataIndex: "status", key: "status",
              render: (s: string) => <Tag color={WO_STATUS_COLOR[s]}>{s}</Tag>,
            },
            { title: "Station Seq", dataIndex: "current_station_sequence", key: "seq" },
            {
              title: "Actions", key: "actions",
              render: (_: any, r: WorkOrder) => r.status !== "completed" ? (
                <Space>
                  <Button size="small" onClick={() => advance(r.id)}>Advance</Button>
                  <Button size="small" type="primary" onClick={() => complete(r.id)}>Complete</Button>
                </Space>
              ) : <Tag color="success">Done</Tag>,
            },
          ]}
        />
      </Card>

      <Card title="Inventory Reservations">
        <Table
          rowKey="id" size="small"
          dataSource={reservations}
          columns={[
            { title: "Product", dataIndex: "product_name", key: "product" },
            { title: "Reserved Qty", dataIndex: "quantity_reserved", key: "qty" },
            { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
          ]}
        />
      </Card>
    </div>
  );
}
