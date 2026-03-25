import { Button, Space, Table, Tag, Typography, message } from "antd";
import React, { useEffect, useState } from "react";
import { Invoice, invoicesApi } from "../api/invoices";
import EmptyState from "../components/EmptyState";

const { Title } = Typography;

const STATUS_COLOR: Record<string, string> = {
  draft: "default",
  sent: "processing",
  paid: "success",
};

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setInvoices(await invoicesApi.list()); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const updateStatus = async (id: number, status: string) => {
    try { await invoicesApi.updateStatus(id, status); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const expandedRowRender = (record: Invoice) => (
    <Table
      rowKey="id"
      size="small"
      dataSource={record.line_items}
      pagination={false}
      columns={[
        { title: "Description", dataIndex: "description", key: "desc" },
        { title: "Qty", dataIndex: "quantity", key: "qty" },
        { title: "Unit Price", dataIndex: "unit_price", key: "price", render: (v: number) => `$${Number(v).toFixed(2)}` },
        { title: "Subtotal", dataIndex: "subtotal", key: "subtotal", render: (v: number) => `$${Number(v).toFixed(2)}` },
      ]}
    />
  );

  const columns = [
    { title: "Invoice #", dataIndex: "invoice_number", key: "inv_num" },
    { title: "Order", dataIndex: "order_id", key: "order", render: (v: number) => `#${v}` },
    { title: "Shipment", dataIndex: "shipment_id", key: "shipment", render: (v: number) => `#${v}` },
    {
      title: "Status", dataIndex: "status", key: "status",
      render: (s: string) => <Tag color={STATUS_COLOR[s] || "default"}>{s.toUpperCase()}</Tag>,
    },
    { title: "Subtotal", dataIndex: "subtotal", key: "subtotal", render: (v: number) => `$${Number(v).toFixed(2)}` },
    { title: "Tax", dataIndex: "tax_amount", key: "tax", render: (v: number) => `$${Number(v).toFixed(2)}` },
    { title: "Total", dataIndex: "total_amount", key: "total", render: (v: number) => `$${Number(v).toFixed(2)}` },
    { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
    {
      title: "Actions", key: "actions",
      render: (_: any, r: Invoice) => (
        <Space>
          {r.status === "draft" && (
            <Button size="small" type="primary" onClick={() => updateStatus(r.id, "sent")}>Mark Sent</Button>
          )}
          {r.status === "sent" && (
            <Button size="small" type="primary" onClick={() => updateStatus(r.id, "paid")}>Mark Paid</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>Invoices</Title>
      {!loading && invoices.length === 0 ? (
        <EmptyState
          title="No invoices yet"
          description="Invoices are auto-generated when a shipment is created."
          workflowHint="Ship an order to see its invoice appear here."
        />
      ) : (
        <Table
          rowKey="id"
          dataSource={invoices}
          columns={columns}
          loading={loading}
          expandable={{ expandedRowRender, rowExpandable: (r) => r.line_items.length > 0 }}
        />
      )}
    </div>
  );
}
