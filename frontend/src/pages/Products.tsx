import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button, Drawer, Form, Input, InputNumber, Popconfirm,
  Space, Table, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Product, productsApi } from "../api/products";

const { Title } = Typography;

export default function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try { setProducts(await productsApi.list()); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); form.resetFields(); setDrawerOpen(true); };
  const openEdit = (p: Product) => { setEditing(p); form.setFieldsValue(p); setDrawerOpen(true); };

  const onSave = async () => {
    const values = await form.validateFields();
    try {
      if (editing) await productsApi.update(editing.id, values);
      else await productsApi.create(values);
      message.success("Saved");
      setDrawerOpen(false);
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const onDelete = async (id: number) => {
    try { await productsApi.delete(id); message.success("Deleted"); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const columns = [
    { title: "SKU", dataIndex: "sku", key: "sku" },
    {
      title: "Name", dataIndex: "name", key: "name",
      render: (name: string, r: Product) => (
        <Button type="link" onClick={() => navigate(`/products/${r.id}`)}>{name}</Button>
      ),
    },
    { title: "Price", dataIndex: "unit_price", key: "unit_price", render: (v: number) => `$${Number(v).toFixed(2)}` },
    { title: "Cost", dataIndex: "unit_cost", key: "unit_cost", render: (v: number) => `$${Number(v).toFixed(2)}` },
    { title: "UOM", dataIndex: "unit_of_measure", key: "uom" },
    {
      title: "Actions", key: "actions",
      render: (_: any, r: Product) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(r)} />
          <Popconfirm title="Delete product?" onConfirm={() => onDelete(r.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Products</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>New Product</Button>
      </div>
      <Table rowKey="id" dataSource={products} columns={columns} loading={loading} />
      <Drawer
        title={editing ? "Edit Product" : "New Product"}
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
          <Form.Item name="sku" label="SKU" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="unit_price" label="Unit Price" initialValue={0}><InputNumber min={0} precision={4} style={{ width: "100%" }} prefix="$" /></Form.Item>
          <Form.Item name="unit_cost" label="Unit Cost" initialValue={0}><InputNumber min={0} precision={4} style={{ width: "100%" }} prefix="$" /></Form.Item>
          <Form.Item name="unit_of_measure" label="UOM" initialValue="EA"><Input /></Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
