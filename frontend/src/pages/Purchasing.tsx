import { Button, Select, Space, Table, Tag, Typography, message } from "antd";
import React, { useEffect, useState } from "react";
import { PurchaseRequest, purchasingApi } from "../api/purchasing";
import EmptyState from "../components/EmptyState";

const { Title } = Typography;

const STATUS_COLOR: Record<string, string> = {
  pending: "default",
  ordered: "processing",
  received: "success",
};

export default function Purchasing() {
  const [requests, setRequests] = useState<PurchaseRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  const load = async () => {
    setLoading(true);
    try { setRequests(await purchasingApi.list(statusFilter)); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [statusFilter]);

  const updateStatus = async (id: number, status: string) => {
    try { await purchasingApi.updateStatus(id, status); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const columns = [
    { title: "ID", dataIndex: "id", key: "id" },
    { title: "Order", dataIndex: "order_id", key: "order", render: (v: number) => `#${v}` },
    { title: "SKU", dataIndex: "product_sku", key: "sku" },
    { title: "Product", dataIndex: "product_name", key: "product" },
    { title: "Qty Needed", dataIndex: "quantity_needed", key: "qty", render: (v: number) => Number(v).toFixed(2) },
    {
      title: "Status", dataIndex: "status", key: "status",
      render: (s: string) => <Tag color={STATUS_COLOR[s] || "default"}>{s.toUpperCase()}</Tag>,
    },
    { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: "Actions", key: "actions",
      render: (_: any, r: PurchaseRequest) => (
        <Space>
          {r.status === "pending" && (
            <Button size="small" type="primary" onClick={() => updateStatus(r.id, "ordered")}>Mark Ordered</Button>
          )}
          {r.status === "ordered" && (
            <Button size="small" type="primary" onClick={() => updateStatus(r.id, "received")}>Mark Received</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Purchase Requests</Title>
        <Select
          allowClear placeholder="Filter by status" style={{ width: 200 }}
          value={statusFilter}
          onChange={setStatusFilter}
          options={["pending", "ordered", "received"].map((s) => ({ value: s, label: s }))}
        />
      </div>
      {!loading && requests.length === 0 ? (
        <EmptyState
          title="No purchase requests"
          description="Purchase requests are auto-generated when inventory is short during order conversion."
          workflowHint="Convert an order with insufficient inventory to see purchase requests appear."
        />
      ) : (
        <Table rowKey="id" dataSource={requests} columns={columns} loading={loading} />
      )}
    </div>
  );
}
