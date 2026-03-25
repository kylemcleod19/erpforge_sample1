import { Button, Select, Space, Table, Tag, Typography } from "antd";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Order, ordersApi } from "../api/orders";
import EmptyState from "../components/EmptyState";

const { Title } = Typography;

const STATUS_COLOR: Record<string, string> = {
  pending: "blue", in_progress: "processing", shipped: "cyan",
  invoiced: "green", cancelled: "red",
};

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try { setOrders(await ordersApi.list(statusFilter)); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [statusFilter]);

  const columns = [
    {
      title: "ID", dataIndex: "id", key: "id",
      render: (id: number) => <Button type="link" onClick={() => navigate(`/orders/${id}`)}>#{id}</Button>,
    },
    { title: "Quote", dataIndex: "quote_id", key: "quote", render: (v: number | null) => v ? `#${v}` : "—" },
    {
      title: "Status", dataIndex: "status", key: "status",
      render: (s: string) => <Tag color={STATUS_COLOR[s] || "default"}>{s.toUpperCase()}</Tag>,
    },
    { title: "Items", key: "items", render: (_: any, r: Order) => r.line_items.length },
    { title: "Created", dataIndex: "created_at", key: "created_at", render: (v: string) => new Date(v).toLocaleDateString() },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Orders</Title>
        <Select
          allowClear placeholder="Filter by status" style={{ width: 200 }}
          value={statusFilter}
          onChange={(v) => setStatusFilter(v)}
          options={["pending", "in_progress", "shipped", "invoiced", "cancelled"].map((s) => ({ value: s, label: s }))}
        />
      </div>
      {!loading && orders.length === 0 ? (
        <EmptyState
          title="No orders yet"
          description="Orders are created when a quote is won and converted."
          workflowHint="Win a quote first, then convert it to generate orders, reservations, and work orders."
          actionLabel="Go to Quotes"
          onAction={() => navigate("/quotes")}
        />
      ) : (
        <Table rowKey="id" dataSource={orders} columns={columns} loading={loading} />
      )}
    </div>
  );
}
