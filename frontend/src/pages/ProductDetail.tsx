import { DeleteOutlined, LinkOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button, Card, Descriptions, Form, Input, InputNumber, Popconfirm,
  Select, Space, Table, Tree, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { BOMItem, CostNode, Product, ProductSpec, productsApi } from "../api/products";

const { Title } = Typography;

function CostTree({ node }: { node: CostNode }) {
  const treeData = [{
    title: `${node.name} (${node.sku}) — own: $${Number(node.unit_cost).toFixed(4)}, rolled up: $${Number(node.rolled_up_cost).toFixed(4)}`,
    key: `${node.product_id}`,
    children: node.children.map((c) => buildTreeNode(c)),
  }];

  function buildTreeNode(n: CostNode): any {
    return {
      title: `${n.name} (${n.sku}) — own: $${Number(n.unit_cost).toFixed(4)}, rolled up: $${Number(n.rolled_up_cost).toFixed(4)}`,
      key: `${n.product_id}-${Math.random()}`,
      children: n.children.map(buildTreeNode),
    };
  }

  return <Tree treeData={treeData} defaultExpandAll />;
}

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const pid = parseInt(id!);

  const [product, setProduct] = useState<Product | null>(null);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [costNode, setCostNode] = useState<CostNode | null>(null);
  const [bomForm] = Form.useForm();
  const [specForm] = Form.useForm();

  const load = async () => {
    const [p, all, cost] = await Promise.all([
      productsApi.get(pid),
      productsApi.list(),
      productsApi.getCost(pid).catch(() => null),
    ]);
    setProduct(p);
    setAllProducts(all);
    setCostNode(cost);
  };

  useEffect(() => { load(); }, [pid]);

  const addBOM = async () => {
    const vals = await bomForm.validateFields();
    try {
      await productsApi.addBOMItem(pid, vals);
      message.success("BOM item added");
      bomForm.resetFields();
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const removeBOM = async (bomItemId: number) => {
    try {
      await productsApi.removeBOMItem(pid, bomItemId);
      message.success("Removed");
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const addSpec = async () => {
    const vals = await specForm.validateFields();
    try {
      await productsApi.addSpec(pid, vals);
      message.success("Spec added");
      specForm.resetFields();
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const removeSpec = async (specId: number) => {
    try {
      await productsApi.removeSpec(pid, specId);
      message.success("Removed");
      load();
    } catch (e: any) { message.error(e.message); }
  };

  if (!product) return <div>Loading...</div>;

  const otherProducts = allProducts.filter((p) => p.id !== pid);

  return (
    <div>
      <Title level={3}>{product.name}</Title>
      <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="SKU">{product.sku}</Descriptions.Item>
        <Descriptions.Item label="UOM">{product.unit_of_measure}</Descriptions.Item>
        <Descriptions.Item label="Unit Price">${Number(product.unit_price).toFixed(4)}</Descriptions.Item>
        <Descriptions.Item label="Unit Cost">${Number(product.unit_cost).toFixed(4)}</Descriptions.Item>
        <Descriptions.Item label="Description" span={2}>{product.description || "—"}</Descriptions.Item>
      </Descriptions>

      <Card title="Bill of Materials" style={{ marginBottom: 24 }}>
        <Form form={bomForm} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item name="child_product_id" label="Component" rules={[{ required: true }]}>
            <Select style={{ width: 200 }} showSearch optionFilterProp="label"
              options={otherProducts.map((p) => ({ value: p.id, label: `${p.sku} — ${p.name}` }))} />
          </Form.Item>
          <Form.Item name="quantity" label="Qty" rules={[{ required: true }]}>
            <InputNumber min={0.0001} precision={4} />
          </Form.Item>
          <Form.Item name="unit_of_measure" label="UOM" initialValue="EA">
            <Input style={{ width: 80 }} />
          </Form.Item>
          <Button type="primary" icon={<PlusOutlined />} onClick={addBOM}>Add</Button>
        </Form>
        <Table
          rowKey="id"
          size="small"
          dataSource={product.bom_items}
          columns={[
            { title: "SKU", dataIndex: "child_product_sku", key: "sku" },
            { title: "Name", dataIndex: "child_product_name", key: "name" },
            { title: "Qty", dataIndex: "quantity", key: "qty" },
            { title: "UOM", dataIndex: "unit_of_measure", key: "uom" },
            {
              title: "", key: "del",
              render: (_: any, r: BOMItem) => (
                <Popconfirm title="Remove?" onConfirm={() => removeBOM(r.id)}>
                  <Button icon={<DeleteOutlined />} size="small" danger />
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>

      <Card title="Spec URLs" style={{ marginBottom: 24 }}>
        <Form form={specForm} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item name="label" label="Label" rules={[{ required: true }]}>
            <Input style={{ width: 160 }} />
          </Form.Item>
          <Form.Item name="url" label="URL" rules={[{ required: true }]}>
            <Input style={{ width: 300 }} />
          </Form.Item>
          <Button type="primary" icon={<PlusOutlined />} onClick={addSpec}>Add</Button>
        </Form>
        <Table
          rowKey="id"
          size="small"
          dataSource={product.specs}
          columns={[
            { title: "Label", dataIndex: "label", key: "label" },
            {
              title: "URL", dataIndex: "url", key: "url",
              render: (url: string) => <a href={url} target="_blank" rel="noreferrer"><LinkOutlined /> {url}</a>,
            },
            {
              title: "", key: "del",
              render: (_: any, r: ProductSpec) => (
                <Popconfirm title="Remove?" onConfirm={() => removeSpec(r.id)}>
                  <Button icon={<DeleteOutlined />} size="small" danger />
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>

      {costNode && (
        <Card title="Cost Rollup">
          <CostTree node={costNode} />
        </Card>
      )}
    </div>
  );
}
