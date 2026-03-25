import { Button, Select, Space, Table, Tag, Typography, message } from "antd";
import React, { useEffect, useState } from "react";
import { manufacturingApi, WorkOrder, WorkOrderLog } from "../api/manufacturing";
import EmptyState from "../components/EmptyState";

const { Title } = Typography;

const STATUS_COLOR: Record<string, string> = {
  queued: "default",
  in_progress: "processing",
  completed: "success",
};

export default function WorkOrders() {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  const load = async () => {
    setLoading(true);
    try {
      setWorkOrders(await manufacturingApi.listWorkOrders(statusFilter ? { status: statusFilter } : {}));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [statusFilter]);

  const advance = async (id: number) => {
    try { await manufacturingApi.advance(id); message.success("Advanced"); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const complete = async (id: number) => {
    try { await manufacturingApi.complete(id); message.success("Completed"); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const expandedRowRender = (record: WorkOrder) => (
    <Table
      rowKey="id"
      size="small"
      dataSource={record.logs}
      pagination={false}
      columns={[
        { title: "Station", dataIndex: "station_name", key: "station" },
        { title: "Operator", dataIndex: "operator", key: "operator", render: (v: string) => v || "—" },
        { title: "Started", dataIndex: "started_at", key: "started", render: (v: string) => v ? new Date(v).toLocaleString() : "—" },
        { title: "Completed", dataIndex: "completed_at", key: "completed", render: (v: string) => v ? new Date(v).toLocaleString() : "—" },
        { title: "Notes", dataIndex: "notes", key: "notes", render: (v: string) => v || "—" },
      ]}
    />
  );

  const columns = [
    { title: "ID", dataIndex: "id", key: "id" },
    { title: "Order", dataIndex: "order_id", key: "order", render: (v: number) => `#${v}` },
    { title: "Product", dataIndex: "product_name", key: "product" },
    { title: "SKU", dataIndex: "product_sku", key: "sku" },
    { title: "Qty", dataIndex: "quantity", key: "qty" },
    {
      title: "Status", dataIndex: "status", key: "status",
      render: (s: string) => <Tag color={STATUS_COLOR[s] || "default"}>{s}</Tag>,
    },
    { title: "Station Seq", dataIndex: "current_station_sequence", key: "seq", render: (v: number | null) => v ?? "—" },
    { title: "BOM Rev", dataIndex: "bom_revision_id", key: "bom_rev", render: (v: number | null) => v ? `#${v}` : "—" },
    { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: "Actions", key: "actions",
      render: (_: any, r: WorkOrder) =>
        r.status !== "completed" ? (
          <Space>
            <Button size="small" onClick={() => advance(r.id)}>Advance</Button>
            <Button size="small" type="primary" onClick={() => complete(r.id)}>Complete</Button>
          </Space>
        ) : (
          <Tag color="success">Done</Tag>
        ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Work Orders</Title>
        <Select
          allowClear placeholder="Filter by status" style={{ width: 200 }}
          value={statusFilter}
          onChange={setStatusFilter}
          options={["queued", "in_progress", "completed"].map((s) => ({ value: s, label: s }))}
        />
      </div>
      {!loading && workOrders.length === 0 ? (
        <EmptyState
          title="No work orders yet"
          description="Work orders track manufacturing progress through your routing stations."
          workflowHint="Work orders are auto-created when a quote converts to an order for products with routings."
        />
      ) : (
        <Table
          rowKey="id"
          dataSource={workOrders}
          columns={columns}
          loading={loading}
          expandable={{ expandedRowRender, rowExpandable: (r) => r.logs.length > 0 }}
        />
      )}
    </div>
  );
}
