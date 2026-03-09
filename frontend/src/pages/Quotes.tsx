import { PlusOutlined } from "@ant-design/icons";
import { Button, Drawer, Form, Input, Space, Table, Tag, Typography, message } from "antd";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Quote, quotesApi } from "../api/quotes";

const { Title } = Typography;

const STATUS_COLOR: Record<string, string> = {
  draft: "default", review: "processing", approved: "cyan",
  sent: "orange", won: "green", lost: "red",
};

export default function Quotes() {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try { setQuotes(await quotesApi.list()); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const onSave = async () => {
    const values = await form.validateFields();
    try {
      await quotesApi.create(values);
      message.success("Quote created");
      setDrawerOpen(false);
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const columns = [
    {
      title: "ID", dataIndex: "id", key: "id",
      render: (id: number) => <Button type="link" onClick={() => navigate(`/quotes/${id}`)}>#{id}</Button>,
    },
    { title: "Customer", dataIndex: "customer_name", key: "customer" },
    {
      title: "Status", dataIndex: "status", key: "status",
      render: (s: string) => <Tag color={STATUS_COLOR[s] || "default"}>{s.toUpperCase()}</Tag>,
    },
    {
      title: "Total", key: "total",
      render: (_: any, r: Quote) => {
        const total = r.line_items.reduce((sum, li) => sum + Number(li.subtotal), 0);
        return `$${total.toFixed(2)}`;
      },
    },
    { title: "Created", dataIndex: "created_at", key: "created_at", render: (v: string) => new Date(v).toLocaleDateString() },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Quotes</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setDrawerOpen(true); }}>New Quote</Button>
      </div>
      <Table rowKey="id" dataSource={quotes} columns={columns} loading={loading} />
      <Drawer
        title="New Quote"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        footer={
          <Space style={{ float: "right" }}>
            <Button onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button type="primary" onClick={onSave}>Create</Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="customer_name" label="Customer Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="customer_email" label="Customer Email"><Input type="email" /></Form.Item>
          <Form.Item name="notes" label="Notes"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
