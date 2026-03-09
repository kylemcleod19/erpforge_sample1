import { PlusOutlined } from "@ant-design/icons";
import {
  Button, DatePicker, Drawer, Form, Input, InputNumber, Space,
  Table, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { Shipment, shippingApi } from "../api/shipping";

const { Title } = Typography;

export default function Shipping() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try { setShipments(await shippingApi.list()); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const onSave = async () => {
    const values = await form.validateFields();
    const payload = {
      ...values,
      shipped_at: values.shipped_at ? values.shipped_at.toISOString() : undefined,
    };
    try {
      await shippingApi.create(payload);
      message.success("Shipment created and invoice generated");
      setDrawerOpen(false);
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const columns = [
    { title: "ID", dataIndex: "id", key: "id" },
    { title: "Order", dataIndex: "order_id", key: "order", render: (v: number) => `#${v}` },
    { title: "Carrier", dataIndex: "carrier", key: "carrier", render: (v: string) => v || "—" },
    { title: "Tracking", dataIndex: "tracking_number", key: "tracking", render: (v: string) => v || "—" },
    { title: "Shipped At", dataIndex: "shipped_at", key: "shipped", render: (v: string) => v ? new Date(v).toLocaleString() : "—" },
    { title: "Notes", dataIndex: "notes", key: "notes", render: (v: string) => v || "—" },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Shipments</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setDrawerOpen(true); }}>
          New Shipment
        </Button>
      </div>
      <Table rowKey="id" dataSource={shipments} columns={columns} loading={loading} />
      <Drawer
        title="Create Shipment"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        footer={
          <Space style={{ float: "right" }}>
            <Button onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button type="primary" onClick={onSave}>Create (+ Generate Invoice)</Button>
          </Space>
        }
      >
        <Typography.Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
          Creating a shipment will automatically generate a draft invoice.
        </Typography.Text>
        <Form form={form} layout="vertical">
          <Form.Item name="order_id" label="Order ID" rules={[{ required: true }]}>
            <InputNumber style={{ width: "100%" }} min={1} />
          </Form.Item>
          <Form.Item name="carrier" label="Carrier"><Input /></Form.Item>
          <Form.Item name="shipping_account_number" label="Account Number"><Input /></Form.Item>
          <Form.Item name="tracking_number" label="Tracking Number"><Input /></Form.Item>
          <Form.Item name="shipped_at" label="Shipped At"><DatePicker showTime style={{ width: "100%" }} /></Form.Item>
          <Form.Item name="notes" label="Notes"><Input.TextArea rows={3} /></Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
