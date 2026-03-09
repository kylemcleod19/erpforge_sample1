import { EditOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button, Card, Drawer, Form, InputNumber, Select, Space,
  Table, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { InventoryBalance, InventoryReservation, inventoryApi } from "../api/inventory";
import { Product, productsApi } from "../api/products";

const { Title } = Typography;

export default function Inventory() {
  const [balances, setBalances] = useState<InventoryBalance[]>([]);
  const [reservations, setReservations] = useState<InventoryReservation[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<InventoryBalance | null>(null);
  const [form] = Form.useForm();

  const load = async () => {
    const [b, r, p] = await Promise.all([
      inventoryApi.listBalances(),
      inventoryApi.listReservations(),
      productsApi.list(),
    ]);
    setBalances(b);
    setReservations(r);
    setProducts(p);
  };

  useEffect(() => { load(); }, []);

  const openEdit = (b: InventoryBalance) => {
    setEditing(b);
    form.setFieldsValue({ product_id: b.product_id, quantity_on_hand: Number(b.quantity_on_hand) });
    setDrawerOpen(true);
  };

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    setDrawerOpen(true);
  };

  const onSave = async () => {
    const values = await form.validateFields();
    try {
      await inventoryApi.upsertBalance(values);
      message.success("Saved");
      setDrawerOpen(false);
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const balanceColumns = [
    { title: "SKU", dataIndex: "product_sku", key: "sku" },
    { title: "Product", dataIndex: "product_name", key: "name" },
    { title: "On Hand", dataIndex: "quantity_on_hand", key: "qty", render: (v: number) => Number(v).toFixed(2) },
    {
      title: "Actions", key: "actions",
      render: (_: any, r: InventoryBalance) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(r)}>Edit</Button>
      ),
    },
  ];

  const reservationColumns = [
    { title: "Order", dataIndex: "order_id", key: "order", render: (v: number) => `#${v}` },
    { title: "Product", dataIndex: "product_name", key: "product" },
    { title: "Reserved Qty", dataIndex: "quantity_reserved", key: "qty", render: (v: number) => Number(v).toFixed(2) },
    { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
  ];

  return (
    <div>
      <Title level={3}>Inventory</Title>

      <Card
        title="Balances"
        style={{ marginBottom: 24 }}
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Set Balance</Button>}
      >
        <Table rowKey="id" dataSource={balances} columns={balanceColumns} size="small" />
      </Card>

      <Card title="Reservations">
        <Table rowKey="id" dataSource={reservations} columns={reservationColumns} size="small" />
      </Card>

      <Drawer
        title={editing ? "Edit Balance" : "Set Balance"}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        footer={
          <Space style={{ float: "right" }}>
            <Button onClick={() => setDrawerOpen(false)}>Cancel</Button>
            <Button type="primary" onClick={onSave}>Save</Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item name="product_id" label="Product" rules={[{ required: true }]}>
            <Select
              showSearch
              optionFilterProp="label"
              disabled={!!editing}
              options={products.map((p) => ({ value: p.id, label: `${p.sku} — ${p.name}` }))}
            />
          </Form.Item>
          <Form.Item name="quantity_on_hand" label="Quantity On Hand" rules={[{ required: true }]}>
            <InputNumber min={0} precision={4} style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
