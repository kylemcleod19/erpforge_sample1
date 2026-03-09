import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button, Card, Drawer, Form, Input, InputNumber,
  Popconfirm, Select, Space, Table, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { manufacturingApi, WorkStation, ProductRouting } from "../api/manufacturing";
import { productsApi, Product } from "../api/products";

const { Title } = Typography;

export default function Stations() {
  const [stations, setStations] = useState<WorkStation[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<WorkStation | null>(null);
  const [form] = Form.useForm();

  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [routing, setRouting] = useState<ProductRouting | null>(null);
  const [routingStationIds, setRoutingStationIds] = useState<number[]>([]);
  const [savingRouting, setSavingRouting] = useState(false);

  const loadStations = async () => {
    const s = await manufacturingApi.listStations();
    setStations(s);
  };

  const loadProducts = async () => {
    setProducts(await productsApi.list());
  };

  useEffect(() => { loadStations(); loadProducts(); }, []);

  useEffect(() => {
    if (selectedProductId) {
      manufacturingApi.getRouting(selectedProductId).then((r) => {
        setRouting(r);
        setRoutingStationIds(r.routing.map((e) => e.station_id));
      });
    } else {
      setRouting(null);
      setRoutingStationIds([]);
    }
  }, [selectedProductId]);

  const openCreate = () => { setEditing(null); form.resetFields(); setDrawerOpen(true); };
  const openEdit = (s: WorkStation) => { setEditing(s); form.setFieldsValue(s); setDrawerOpen(true); };

  const onSave = async () => {
    const values = await form.validateFields();
    try {
      if (editing) await manufacturingApi.updateStation(editing.id, values);
      else await manufacturingApi.createStation(values);
      message.success("Saved");
      setDrawerOpen(false);
      loadStations();
    } catch (e: any) { message.error(e.message); }
  };

  const onDelete = async (id: number) => {
    try { await manufacturingApi.deleteStation(id); message.success("Deleted"); loadStations(); }
    catch (e: any) { message.error(e.message); }
  };

  const saveRouting = async () => {
    if (!selectedProductId) return;
    setSavingRouting(true);
    try {
      await manufacturingApi.setRouting(selectedProductId, routingStationIds);
      message.success("Routing saved");
    } catch (e: any) { message.error(e.message); }
    finally { setSavingRouting(false); }
  };

  const stationColumns = [
    { title: "Name", dataIndex: "name", key: "name" },
    { title: "Description", dataIndex: "description", key: "desc", render: (v: string) => v || "—" },
    { title: "Sequence", dataIndex: "sequence", key: "seq" },
    {
      title: "Actions", key: "actions",
      render: (_: any, r: WorkStation) => (
        <Space>
          <Button icon={<EditOutlined />} size="small" onClick={() => openEdit(r)} />
          <Popconfirm title="Delete station?" onConfirm={() => onDelete(r.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>Stations & Routing</Title>

      <Card
        title="Work Stations"
        style={{ marginBottom: 24 }}
        extra={<Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>New Station</Button>}
      >
        <Table rowKey="id" dataSource={stations} columns={stationColumns} size="small" />
      </Card>

      <Card title="Product Routing">
        <div style={{ marginBottom: 16 }}>
          <Select
            style={{ width: 300 }}
            placeholder="Select a product to configure routing"
            showSearch
            optionFilterProp="label"
            value={selectedProductId ?? undefined}
            onChange={(v) => setSelectedProductId(v)}
            options={products.map((p) => ({ value: p.id, label: `${p.sku} — ${p.name}` }))}
          />
        </div>
        {selectedProductId && (
          <div>
            <div style={{ marginBottom: 8 }}>
              <Typography.Text type="secondary">
                Select stations in order (top = first station):
              </Typography.Text>
            </div>
            <Select
              mode="multiple"
              style={{ width: "100%", marginBottom: 12 }}
              placeholder="Select stations in routing order"
              value={routingStationIds}
              onChange={setRoutingStationIds}
              options={stations.map((s) => ({ value: s.id, label: `${s.name} (seq: ${s.sequence})` }))}
            />
            <Button type="primary" loading={savingRouting} onClick={saveRouting}>
              Save Routing
            </Button>
          </div>
        )}
      </Card>

      <Drawer
        title={editing ? "Edit Station" : "New Station"}
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
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="sequence" label="Default Sequence" initialValue={0}><InputNumber style={{ width: "100%" }} /></Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
