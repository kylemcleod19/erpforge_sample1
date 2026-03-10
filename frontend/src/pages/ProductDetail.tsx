import { DeleteOutlined, LinkOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Alert, Badge, Button, Card, Descriptions, Form, Input, InputNumber, Modal,
  Popconfirm, Select, Space, Table, Tag, Tree, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  BOMItem, BOMItemAlternate, BOMRevision, CostNode,
  Product, ProductCompliance, ProductSpec, productsApi
} from "../api/products";

const { Title } = Typography;

const LIFECYCLE_COLORS: Record<string, string> = {
  prototype: "blue",
  production: "green",
  end_of_life: "red",
};

const REVISION_STATUS_COLORS: Record<string, string> = {
  draft: "default",
  pending_approval: "processing",
  approved: "success",
  superseded: "warning",
};

function CostTree({ node }: { node: CostNode }) {
  function buildTreeNode(n: CostNode): any {
    return {
      title: `${n.name} (${n.sku}) — own: $${Number(n.unit_cost).toFixed(4)}, rolled up: $${Number(n.rolled_up_cost).toFixed(4)}`,
      key: `${n.product_id}-${Math.random()}`,
      children: n.children.map(buildTreeNode),
    };
  }

  const treeData = [buildTreeNode(node)];
  return <Tree treeData={treeData} defaultExpandAll />;
}

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const pid = parseInt(id!);

  const [product, setProduct] = useState<Product | null>(null);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [costNode, setCostNode] = useState<CostNode | null>(null);

  // Phase 2: BOM revisions
  const [revisions, setRevisions] = useState<BOMRevision[]>([]);
  const [selectedRevId, setSelectedRevId] = useState<number | undefined>();
  const [revBOMItems, setRevBOMItems] = useState<BOMItem[]>([]);
  const [newRevForm] = Form.useForm();
  const [newRevModalOpen, setNewRevModalOpen] = useState(false);
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [approveRevId, setApproveRevId] = useState<number | undefined>();
  const [approveForm] = Form.useForm();

  // Phase 3: BOM line enrichment
  const [bomForm] = Form.useForm();
  const [alternates, setAlternates] = useState<Record<number, BOMItemAlternate[]>>({});
  const [altModalOpen, setAltModalOpen] = useState(false);
  const [altBOMItemId, setAltBOMItemId] = useState<number | undefined>();
  const [altForm] = Form.useForm();

  // Specs
  const [specForm] = Form.useForm();

  // Phase 4: Compliance
  const [compliance, setCompliance] = useState<ProductCompliance[]>([]);
  const [complianceForm] = Form.useForm();

  const load = async () => {
    const [p, all, cost, revs, comp] = await Promise.all([
      productsApi.get(pid),
      productsApi.list(),
      productsApi.getCost(pid).catch(() => null),
      productsApi.listRevisions(pid),
      productsApi.listCompliance(pid),
    ]);
    setProduct(p);
    setAllProducts(all);
    setCostNode(cost);
    setRevisions(revs);
    setCompliance(comp);
  };

  const loadRevBOM = async (revId: number) => {
    const items = await productsApi.getBOMForRevision(pid, revId);
    setRevBOMItems(items);
  };

  useEffect(() => { load(); }, [pid]);

  useEffect(() => {
    if (selectedRevId !== undefined) {
      loadRevBOM(selectedRevId);
    }
  }, [selectedRevId]);

  // ---- BOM (unscoped) ----

  const addBOM = async () => {
    const vals = await bomForm.validateFields();
    try {
      const result = await productsApi.addBOMItem(pid, vals);
      if (result.warnings && result.warnings.length > 0) {
        result.warnings.forEach((w) => message.warning(w, 6));
      }
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

  // ---- Alternates ----

  const openAltModal = async (bomItemId: number) => {
    setAltBOMItemId(bomItemId);
    altForm.resetFields();
    const alts = await productsApi.listAlternates(pid, bomItemId);
    setAlternates((prev) => ({ ...prev, [bomItemId]: alts }));
    setAltModalOpen(true);
  };

  const addAlternate = async () => {
    if (!altBOMItemId) return;
    const vals = await altForm.validateFields();
    try {
      await productsApi.addAlternate(pid, altBOMItemId, vals);
      message.success("Alternate added");
      const alts = await productsApi.listAlternates(pid, altBOMItemId);
      setAlternates((prev) => ({ ...prev, [altBOMItemId]: alts }));
      altForm.resetFields();
    } catch (e: any) { message.error(e.message); }
  };

  const removeAlternate = async (bomItemId: number, altId: number) => {
    try {
      await productsApi.removeAlternate(pid, bomItemId, altId);
      const alts = await productsApi.listAlternates(pid, bomItemId);
      setAlternates((prev) => ({ ...prev, [bomItemId]: alts }));
    } catch (e: any) { message.error(e.message); }
  };

  // ---- BOM revisions ----

  const createRevision = async () => {
    const vals = await newRevForm.validateFields();
    try {
      await productsApi.createRevision(pid, vals);
      message.success("Revision created");
      setNewRevModalOpen(false);
      newRevForm.resetFields();
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const openApprove = (revId: number) => {
    setApproveRevId(revId);
    approveForm.resetFields();
    setApproveModalOpen(true);
  };

  const approveRevision = async () => {
    if (!approveRevId) return;
    const vals = await approveForm.validateFields();
    try {
      await productsApi.approveRevision(pid, approveRevId, vals.approved_by);
      message.success("Revision approved");
      setApproveModalOpen(false);
      load();
    } catch (e: any) { message.error(e.message); }
  };

  // ---- Specs ----

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
      load();
    } catch (e: any) { message.error(e.message); }
  };

  // ---- Compliance ----

  const addCompliance = async () => {
    const vals = await complianceForm.validateFields();
    try {
      await productsApi.addCompliance(pid, vals);
      message.success("Compliance record added");
      complianceForm.resetFields();
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const removeCompliance = async (certId: number) => {
    try {
      await productsApi.removeCompliance(pid, certId);
      load();
    } catch (e: any) { message.error(e.message); }
  };

  if (!product) return <div>Loading...</div>;

  const otherProducts = allProducts.filter((p) => p.id !== pid);

  const bomColumns = [
    { title: "SKU", dataIndex: "child_product_sku", key: "sku" },
    { title: "Name", dataIndex: "child_product_name", key: "name" },
    { title: "Qty", dataIndex: "quantity", key: "qty" },
    { title: "UOM", dataIndex: "unit_of_measure", key: "uom" },
    { title: "Ref Des", dataIndex: "reference_designator", key: "refdes", render: (v: string) => v || "—" },
    {
      title: "Type", dataIndex: "component_type", key: "comptype",
      render: (v: string) => v ? <Tag>{v}</Tag> : "—",
    },
    {
      title: "", key: "actions",
      render: (_: any, r: BOMItem) => (
        <Space>
          <Button size="small" onClick={() => openAltModal(r.id)}>
            Alternates
            {alternates[r.id]?.length ? <Badge count={alternates[r.id].length} size="small" style={{ marginLeft: 4 }} /> : null}
          </Button>
          <Popconfirm title="Remove?" onConfirm={() => removeBOM(r.id)}>
            <Button icon={<DeleteOutlined />} size="small" danger />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>{product.name}</Title>

      {/* Phase 1: enriched product header */}
      <Descriptions bordered column={3} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="SKU">{product.sku}</Descriptions.Item>
        <Descriptions.Item label="UOM">{product.unit_of_measure}</Descriptions.Item>
        <Descriptions.Item label="Revision">Rev {product.revision}</Descriptions.Item>
        <Descriptions.Item label="Unit Price">${Number(product.unit_price).toFixed(4)}</Descriptions.Item>
        <Descriptions.Item label="Unit Cost">${Number(product.unit_cost).toFixed(4)}</Descriptions.Item>
        <Descriptions.Item label="Category">{product.category || "—"}</Descriptions.Item>
        <Descriptions.Item label="Lifecycle">
          <Tag color={LIFECYCLE_COLORS[product.lifecycle_status] || "default"}>
            {product.lifecycle_status}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Make/Buy">{product.make_buy}</Descriptions.Item>
        <Descriptions.Item label="Traceability">{product.traceability_type}</Descriptions.Item>
        <Descriptions.Item label="Compliance Required">
          {product.compliance_required ? <Tag color="orange">Yes</Tag> : "No"}
        </Descriptions.Item>
        <Descriptions.Item label="Description" span={2}>{product.description || "—"}</Descriptions.Item>
      </Descriptions>

      {/* Phase 3: BOM line items (unscoped) */}
      <Card title="Bill of Materials" style={{ marginBottom: 24 }}>
        <Form form={bomForm} layout="inline" style={{ marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
          <Form.Item name="child_product_id" label="Component" rules={[{ required: true }]}>
            <Select style={{ width: 200 }} showSearch optionFilterProp="label"
              options={otherProducts.map((p) => ({ value: p.id, label: `${p.sku} — ${p.name}` }))} />
          </Form.Item>
          <Form.Item name="quantity" label="Qty" rules={[{ required: true }]}>
            <InputNumber min={0.0001} precision={4} />
          </Form.Item>
          <Form.Item name="unit_of_measure" label="UOM" initialValue="EA">
            <Input style={{ width: 60 }} />
          </Form.Item>
          <Form.Item name="reference_designator" label="Ref Des">
            <Input style={{ width: 80 }} placeholder="R1, C4…" />
          </Form.Item>
          <Form.Item name="component_type" label="Type">
            <Select style={{ width: 130 }} allowClear
              options={["material", "subassembly", "electronic", "consumable", "service"].map(
                (v) => ({ value: v, label: v }),
              )} />
          </Form.Item>
          <Button type="primary" icon={<PlusOutlined />} onClick={addBOM}>Add</Button>
        </Form>
        <Table rowKey="id" size="small" dataSource={product.bom_items} columns={bomColumns} />
      </Card>

      {/* Phase 2: BOM revisions */}
      <Card
        title="BOM Revisions"
        style={{ marginBottom: 24 }}
        extra={
          <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => setNewRevModalOpen(true)}>
            New Revision
          </Button>
        }
      >
        <Table
          rowKey="id"
          size="small"
          dataSource={revisions}
          pagination={false}
          columns={[
            { title: "Rev #", dataIndex: "revision_number", key: "rev" },
            {
              title: "Status", dataIndex: "status", key: "status",
              render: (s: string) => <Tag color={REVISION_STATUS_COLORS[s] || "default"}>{s}</Tag>,
            },
            { title: "Notes", dataIndex: "notes", key: "notes", render: (v: string) => v || "—" },
            { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
            { title: "Approved By", dataIndex: "approved_by", key: "approved_by", render: (v: string) => v || "—" },
            {
              title: "Actions", key: "actions",
              render: (_: any, r: BOMRevision) => (
                <Space>
                  <Button
                    size="small"
                    onClick={() => setSelectedRevId(r.id === selectedRevId ? undefined : r.id)}
                  >
                    {r.id === selectedRevId ? "Hide BOM" : "View BOM"}
                  </Button>
                  {r.status !== "approved" && r.status !== "superseded" && (
                    <Button size="small" type="primary" onClick={() => openApprove(r.id)}>
                      Approve
                    </Button>
                  )}
                </Space>
              ),
            },
          ]}
        />
        {selectedRevId !== undefined && (
          <div style={{ marginTop: 16 }}>
            <Title level={5} style={{ marginBottom: 8 }}>
              BOM for Revision #{revisions.find((r) => r.id === selectedRevId)?.revision_number}
            </Title>
            <Table
              rowKey="id"
              size="small"
              dataSource={revBOMItems}
              pagination={false}
              columns={[
                { title: "SKU", dataIndex: "child_product_sku", key: "sku" },
                { title: "Name", dataIndex: "child_product_name", key: "name" },
                { title: "Qty", dataIndex: "quantity", key: "qty" },
                { title: "UOM", dataIndex: "unit_of_measure", key: "uom" },
                { title: "Ref Des", dataIndex: "reference_designator", key: "refdes", render: (v: string) => v || "—" },
                { title: "Type", dataIndex: "component_type", key: "type", render: (v: string) => v ? <Tag>{v}</Tag> : "—" },
              ]}
            />
          </div>
        )}
      </Card>

      {/* Phase 4: Compliance */}
      <Card title="Compliance" style={{ marginBottom: 24 }}>
        <Form form={complianceForm} layout="inline" style={{ marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
          <Form.Item name="scope" label="Scope" rules={[{ required: true }]}>
            <Select style={{ width: 130 }}
              options={[{ value: "product", label: "Product" }, { value: "component", label: "Component" }]} />
          </Form.Item>
          <Form.Item name="cert_type" label="Cert Type" rules={[{ required: true }]}>
            <Select style={{ width: 120 }} showSearch
              options={["RoHS", "REACH", "CE", "UL", "FCC", "ISO9001", "Other"].map(
                (v) => ({ value: v, label: v }),
              )} />
          </Form.Item>
          <Form.Item name="cert_number" label="Cert #">
            <Input style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="document_url" label="Doc URL">
            <Input style={{ width: 220 }} />
          </Form.Item>
          <Button type="primary" icon={<PlusOutlined />} onClick={addCompliance}>Add</Button>
        </Form>
        <Table
          rowKey="id"
          size="small"
          dataSource={compliance}
          pagination={false}
          columns={[
            { title: "Scope", dataIndex: "scope", key: "scope" },
            { title: "Cert Type", dataIndex: "cert_type", key: "cert_type", render: (v: string) => <Tag>{v}</Tag> },
            { title: "Cert #", dataIndex: "cert_number", key: "cert_number", render: (v: string) => v || "—" },
            { title: "Issued", dataIndex: "issued_date", key: "issued", render: (v: string) => v || "—" },
            { title: "Expires", dataIndex: "expiry_date", key: "expiry", render: (v: string) => v || "—" },
            {
              title: "Document", dataIndex: "document_url", key: "doc",
              render: (v: string) => v ? <a href={v} target="_blank" rel="noreferrer"><LinkOutlined /> View</a> : "—",
            },
            {
              title: "", key: "del",
              render: (_: any, r: ProductCompliance) => (
                <Popconfirm title="Remove?" onConfirm={() => removeCompliance(r.id)}>
                  <Button icon={<DeleteOutlined />} size="small" danger />
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>

      {/* Spec URLs */}
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

      {/* Cost rollup */}
      {costNode && (
        <Card title="Cost Rollup">
          <CostTree node={costNode} />
        </Card>
      )}

      {/* Modal: new BOM revision */}
      <Modal
        title="New BOM Revision"
        open={newRevModalOpen}
        onOk={createRevision}
        onCancel={() => setNewRevModalOpen(false)}
      >
        <Form form={newRevForm} layout="vertical">
          <Form.Item name="revision_number" label="Revision Number" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal: approve revision */}
      <Modal
        title="Approve BOM Revision"
        open={approveModalOpen}
        onOk={approveRevision}
        onCancel={() => setApproveModalOpen(false)}
      >
        <Form form={approveForm} layout="vertical">
          <Form.Item name="approved_by" label="Approved By" rules={[{ required: true }]}>
            <Input placeholder="Name or engineer ID" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal: alternates */}
      <Modal
        title="Alternate Components"
        open={altModalOpen}
        onCancel={() => setAltModalOpen(false)}
        footer={null}
        width={640}
      >
        <Form form={altForm} layout="inline" style={{ marginBottom: 12 }}>
          <Form.Item name="alternate_product_id" label="Alternate" rules={[{ required: true }]}>
            <Select style={{ width: 220 }} showSearch optionFilterProp="label"
              options={otherProducts.map((p) => ({ value: p.id, label: `${p.sku} — ${p.name}` }))} />
          </Form.Item>
          <Form.Item name="priority" label="Priority" initialValue={1}>
            <InputNumber min={1} style={{ width: 70 }} />
          </Form.Item>
          <Button type="primary" icon={<PlusOutlined />} onClick={addAlternate}>Add</Button>
        </Form>
        {altBOMItemId !== undefined && alternates[altBOMItemId] && (
          <Table
            rowKey="id"
            size="small"
            dataSource={alternates[altBOMItemId]}
            pagination={false}
            columns={[
              { title: "SKU", dataIndex: "alternate_product_sku", key: "sku" },
              { title: "Name", dataIndex: "alternate_product_name", key: "name" },
              { title: "Priority", dataIndex: "priority", key: "priority" },
              { title: "Notes", dataIndex: "notes", key: "notes", render: (v: string) => v || "—" },
              {
                title: "", key: "del",
                render: (_: any, r: BOMItemAlternate) => (
                  <Popconfirm title="Remove?" onConfirm={() => removeAlternate(altBOMItemId, r.id)}>
                    <Button icon={<DeleteOutlined />} size="small" danger />
                  </Popconfirm>
                ),
              },
            ]}
          />
        )}
      </Modal>
    </div>
  );
}
