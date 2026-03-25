import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button, Drawer, Form, Input, InputNumber, Popconfirm, Select,
  Space, Switch, Table, Tag, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Product, productsApi } from "../api/products";
import EmptyState from "../components/EmptyState";

const { Title } = Typography;

const LIFECYCLE_COLORS: Record<string, string> = {
  prototype: "blue",
  production: "green",
  end_of_life: "red",
};

interface ProductsProps {
  itemTypes?: string[];
  pageTitle?: string;
}

export default function Products({ itemTypes, pageTitle = "Products" }: ProductsProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try { setProducts(await productsApi.list(itemTypes)); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [JSON.stringify(itemTypes)]);

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    // Pre-set item_type to first type in the current section
    if (itemTypes?.length) form.setFieldValue("item_type", itemTypes[0]);
    setDrawerOpen(true);
  };
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

  const detailPath = (id: number) =>
    itemTypes?.includes("component") || itemTypes?.includes("raw_material")
      ? `/components/${id}`
      : `/products/${id}`;

  const columns = [
    { title: "SKU", dataIndex: "sku", key: "sku" },
    {
      title: "Name", dataIndex: "name", key: "name",
      render: (name: string, r: Product) => (
        <Button type="link" onClick={() => navigate(detailPath(r.id))}>{name}</Button>
      ),
    },
    { title: "Category", dataIndex: "category", key: "category", render: (v: string) => v || "—" },
    {
      title: "Status", dataIndex: "lifecycle_status", key: "lifecycle_status",
      render: (v: string) => <Tag color={LIFECYCLE_COLORS[v] || "default"}>{v}</Tag>,
    },
    { title: "Item Type", dataIndex: "item_type", key: "item_type" },
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

  const defaultItemType = itemTypes?.[0] ?? "finished_good";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>{pageTitle}</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>New {pageTitle.replace(/s$/, "")}</Button>
      </div>
      {!loading && products.length === 0 ? (
        <EmptyState
          title={`No ${pageTitle.toLowerCase()} yet`}
          description={
            pageTitle === "Components"
              ? "Components are the raw materials and parts used in your bills of materials."
              : "Products represent the finished goods and assemblies your company manufactures."
          }
          workflowHint={
            pageTitle === "Components"
              ? "Components are referenced by BOMs. Add components, then build your bill of materials."
              : "Products are the foundation — create them before BOMs, quotes, or work orders."
          }
          actionLabel={`Create ${pageTitle.replace(/s$/, "")}`}
          onAction={openCreate}
        />
      ) : (
        <Table rowKey="id" dataSource={products} columns={columns} loading={loading} />
      )}
      <Drawer
        title={editing ? `Edit ${pageTitle.replace(/s$/, "")}` : `New ${pageTitle.replace(/s$/, "")}`}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
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
          <Form.Item name="category" label="Category"><Input placeholder="e.g. Electronics, Mechanical" /></Form.Item>
          <Form.Item name="lifecycle_status" label="Lifecycle Status" initialValue="production">
            <Select options={[
              { value: "prototype", label: "Prototype" },
              { value: "production", label: "Production" },
              { value: "end_of_life", label: "End of Life" },
            ]} />
          </Form.Item>
          <Form.Item name="item_type" label="Item Type" initialValue={defaultItemType}>
            <Select options={[
              { value: "finished_good", label: "Finished Good" },
              { value: "assembly", label: "Assembly" },
              { value: "component", label: "Component" },
              { value: "raw_material", label: "Raw Material" },
            ]} />
          </Form.Item>
          <Form.Item name="traceability_type" label="Traceability" initialValue="none">
            <Select options={[
              { value: "none", label: "None" },
              { value: "serial", label: "Serial" },
              { value: "lot", label: "Lot" },
            ]} />
          </Form.Item>
          <Form.Item name="compliance_required" label="Compliance Required" valuePropName="checked" initialValue={false}>
            <Switch />
          </Form.Item>
          <Form.Item name="unit_price" label="Unit Price" initialValue={0}><InputNumber min={0} precision={4} style={{ width: "100%" }} prefix="$" /></Form.Item>
          <Form.Item name="unit_cost" label="Unit Cost" initialValue={0}><InputNumber min={0} precision={4} style={{ width: "100%" }} prefix="$" /></Form.Item>
          <Form.Item name="unit_of_measure" label="UOM" initialValue="EA"><Input /></Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
