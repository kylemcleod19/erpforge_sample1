import { DeleteOutlined, DownloadOutlined, LinkOutlined, PlusOutlined, UploadOutlined } from "@ant-design/icons";
import {
  Alert, Badge, Button, Card, Checkbox, Descriptions, Dropdown, Form, Input, InputNumber, Modal,
  Popconfirm, Select, Space, Table, Tag, Tree, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  BOMConflict, BOMImportPreviewResponse, BOMImportRow,
  BOMItem, BOMItemAlternate, BOMRevision, ColumnDetectResponse, ColumnMapping,
  CostNode, Product, ProductCompliance, ProductSpec, productsApi
} from "../api/products";

const { Title, Text } = Typography;

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

  // BOM CSV import — three-step flow
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvStep, setCsvStep] = useState<1 | 2 | 3>(1);
  const [csvModalOpen, setCsvModalOpen] = useState(false);
  const [csvUploading, setCsvUploading] = useState(false);
  const [csvDetect, setCsvDetect] = useState<ColumnDetectResponse | null>(null);
  const [csvMappings, setCsvMappings] = useState<Record<string, string | null>>({});
  const [csvPreview, setCsvPreview] = useState<BOMImportPreviewResponse | null>(null);
  const [selectedConflicts, setSelectedConflicts] = useState<Set<string>>(new Set());
  const csvInputRef = React.useRef<HTMLInputElement>(null);

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

  // ---- BOM CSV Import — Three-step flow ----

  const resetCsvState = () => {
    setCsvFile(null);
    setCsvStep(1);
    setCsvDetect(null);
    setCsvMappings({});
    setCsvPreview(null);
    setSelectedConflicts(new Set());
  };

  const handleCsvUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setCsvUploading(true);
    try {
      const detect = await productsApi.bomDetectColumns(file);
      setCsvFile(file);
      setCsvDetect(detect);
      // Initialize mappings from suggestions
      const initMappings: Record<string, string | null> = {};
      detect.suggested_mappings.forEach((m) => {
        initMappings[m.csv_column] = m.mapped_to;
      });
      setCsvMappings(initMappings);
      setCsvStep(1);
      setCsvModalOpen(true);
    } catch (e: any) {
      message.error("Upload failed: " + e.message);
    } finally {
      setCsvUploading(false);
    }
  };

  const handlePreviewWithMappings = async () => {
    if (!csvFile) return;
    setCsvUploading(true);
    try {
      // Build overrides: only include mapped columns
      const overrides: Record<string, string> = {};
      for (const [csvCol, field] of Object.entries(csvMappings)) {
        if (field) overrides[csvCol] = field;
      }
      const preview = await productsApi.bomImportPreview(csvFile, overrides);
      if (preview.errors.length > 0 && preview.new_rows.length === 0 && preview.conflicts.length === 0) {
        preview.errors.forEach((err) => message.error(err, 6));
        return;
      }
      setCsvPreview(preview);
      setSelectedConflicts(new Set());
      setCsvStep(2);
      if (preview.errors.length > 0) {
        preview.errors.forEach((err) => message.warning(err, 6));
      }
    } catch (e: any) {
      message.error("Preview failed: " + e.message);
    } finally {
      setCsvUploading(false);
    }
  };

  const handleCsvApply = async () => {
    if (!csvPreview) return;
    const upsertPairs: [string, string][] = Array.from(selectedConflicts).map((key) => {
      const [ps, cs] = key.split("|||");
      return [ps, cs];
    });
    try {
      const result = await productsApi.bomImportApply(
        [...csvPreview.new_rows, ...csvPreview.conflicts.map((c) => ({
          parent_sku: c.parent_sku,
          child_sku: c.child_sku,
          quantity: c.new_quantity,
          ref_designator: c.new_ref_designator,
          line_designator: c.new_line_designator,
          unit_of_measure: c.new_unit_of_measure,
          component_type: c.new_component_type,
          notes: c.new_notes,
          parent_product_id: c.parent_product_id,
          child_product_id: c.child_product_id,
        }))],
        upsertPairs,
      );
      message.success(`Import done: ${result.created} created, ${result.updated} updated, ${result.skipped} skipped`);
      setCsvModalOpen(false);
      resetCsvState();
      load();
    } catch (e: any) {
      message.error("Apply failed: " + e.message);
    }
  };

  // Check if required fields are mapped
  const requiredFields = new Set(["parent_sku", "child_sku", "quantity"]);
  const mappedFields = new Set(Object.values(csvMappings).filter(Boolean));
  const missingRequired = [...requiredFields].filter((f) => !mappedFields.has(f));

  if (!product) return <div>Loading...</div>;

  const otherProducts = allProducts.filter((p) => p.id !== pid);

  const bomColumns = [
    { title: "SKU", dataIndex: "child_product_sku", key: "sku" },
    { title: "Name", dataIndex: "child_product_name", key: "name" },
    { title: "Qty", dataIndex: "quantity", key: "qty" },
    { title: "UOM", dataIndex: "unit_of_measure", key: "uom" },
    { title: "Ref Des", dataIndex: "reference_designator", key: "refdes", render: (v: string) => v || "\u2014" },
    { title: "Line Des", dataIndex: "line_designator", key: "linedes", render: (v: string) => v || "\u2014" },
    {
      title: "Type", dataIndex: "component_type", key: "comptype",
      render: (v: string) => v ? <Tag>{v}</Tag> : "\u2014",
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

  // Build combined rows table for CSV preview step 2
  const previewTableData = csvPreview
    ? [
        ...csvPreview.new_rows.map((r, i) => ({ ...r, _key: `new-${i}`, _status: "new" as const })),
        ...csvPreview.conflicts.map((c, i) => ({
          parent_sku: c.parent_sku,
          child_sku: c.child_sku,
          quantity: c.new_quantity,
          unit_of_measure: c.new_unit_of_measure,
          ref_designator: c.new_ref_designator,
          line_designator: c.new_line_designator,
          component_type: c.new_component_type,
          notes: c.new_notes,
          row_number: undefined as number | undefined,
          _key: `conflict-${i}`,
          _status: "conflict" as const,
          _conflict: c,
        })),
      ]
    : [];

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
        <Descriptions.Item label="Category">{product.category || "\u2014"}</Descriptions.Item>
        <Descriptions.Item label="Lifecycle">
          <Tag color={LIFECYCLE_COLORS[product.lifecycle_status] || "default"}>
            {product.lifecycle_status}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Item Type">{product.item_type}</Descriptions.Item>
        <Descriptions.Item label="Traceability">{product.traceability_type}</Descriptions.Item>
        <Descriptions.Item label="Compliance Required">
          {product.compliance_required ? <Tag color="orange">Yes</Tag> : "No"}
        </Descriptions.Item>
        <Descriptions.Item label="Description" span={2}>{product.description || "\u2014"}</Descriptions.Item>
      </Descriptions>

      {/* Phase 3: BOM line items (unscoped) */}
      <Card
        title="Bill of Materials"
        style={{ marginBottom: 24 }}
        extra={
          <Space>
            <Dropdown
              menu={{
                items: [
                  { key: "pcba", label: "PCBA Template", icon: <DownloadOutlined /> },
                  { key: "mechanical", label: "Mechanical Template", icon: <DownloadOutlined /> },
                ],
                onClick: ({ key }) => productsApi.bomImportTemplate(key as "pcba" | "mechanical"),
              }}
            >
              <Button size="small" icon={<DownloadOutlined />}>Templates</Button>
            </Dropdown>
            <input
              ref={csvInputRef}
              type="file"
              accept=".csv"
              style={{ display: "none" }}
              onChange={handleCsvUpload}
            />
            <Button
              icon={<UploadOutlined />}
              size="small"
              loading={csvUploading}
              onClick={() => csvInputRef.current?.click()}
            >
              Upload BOM CSV
            </Button>
          </Space>
        }
      >
        <Form form={bomForm} layout="inline" style={{ marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
          <Form.Item name="child_product_id" label="Component" rules={[{ required: true }]}>
            <Select style={{ width: 200 }} showSearch optionFilterProp="label"
              options={otherProducts.map((p) => ({ value: p.id, label: `${p.sku} \u2014 ${p.name}` }))} />
          </Form.Item>
          <Form.Item name="quantity" label="Qty" rules={[{ required: true }]}>
            <InputNumber min={0.0001} precision={4} />
          </Form.Item>
          <Form.Item name="unit_of_measure" label="UOM" initialValue="EA">
            <Input style={{ width: 60 }} />
          </Form.Item>
          <Form.Item name="reference_designator" label="Ref Des">
            <Input style={{ width: 80 }} placeholder="R1, C4..." />
          </Form.Item>
          <Form.Item name="line_designator" label="Line Des">
            <Input style={{ width: 80 }} placeholder="1, 2..." />
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
            { title: "Notes", dataIndex: "notes", key: "notes", render: (v: string) => v || "\u2014" },
            { title: "Created", dataIndex: "created_at", key: "created", render: (v: string) => new Date(v).toLocaleDateString() },
            { title: "Approved By", dataIndex: "approved_by", key: "approved_by", render: (v: string) => v || "\u2014" },
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
                { title: "Ref Des", dataIndex: "reference_designator", key: "refdes", render: (v: string) => v || "\u2014" },
                { title: "Line Des", dataIndex: "line_designator", key: "linedes", render: (v: string) => v || "\u2014" },
                { title: "Type", dataIndex: "component_type", key: "type", render: (v: string) => v ? <Tag>{v}</Tag> : "\u2014" },
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
            { title: "Cert #", dataIndex: "cert_number", key: "cert_number", render: (v: string) => v || "\u2014" },
            { title: "Issued", dataIndex: "issued_date", key: "issued", render: (v: string) => v || "\u2014" },
            { title: "Expires", dataIndex: "expiry_date", key: "expiry", render: (v: string) => v || "\u2014" },
            {
              title: "Document", dataIndex: "document_url", key: "doc",
              render: (v: string) => v ? <a href={v} target="_blank" rel="noreferrer"><LinkOutlined /> View</a> : "\u2014",
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

      {/* Modal: BOM CSV Import — Three-step */}
      <Modal
        title={`BOM CSV Import \u2014 Step ${csvStep} of 2`}
        open={csvModalOpen}
        onCancel={() => { setCsvModalOpen(false); resetCsvState(); }}
        width={900}
        footer={
          csvStep === 1 ? (
            <Space>
              <Button onClick={() => { setCsvModalOpen(false); resetCsvState(); }}>Cancel</Button>
              <Button
                type="primary"
                loading={csvUploading}
                disabled={missingRequired.length > 0}
                onClick={handlePreviewWithMappings}
              >
                Preview Import
              </Button>
            </Space>
          ) : (
            <Space>
              <Button onClick={() => setCsvStep(1)}>Back to Mapping</Button>
              <Button onClick={() => { setCsvModalOpen(false); resetCsvState(); }}>Cancel</Button>
              <Button type="primary" onClick={handleCsvApply}>Apply Import</Button>
            </Space>
          )
        }
      >
        {csvStep === 1 && csvDetect && (
          <>
            <Text strong>Map CSV columns to BOM fields</Text>
            {missingRequired.length > 0 && (
              <Alert
                type="error"
                showIcon
                style={{ marginTop: 8, marginBottom: 8 }}
                message={`Required fields not mapped: ${missingRequired.join(", ")}`}
              />
            )}
            <Table
              rowKey="csv_column"
              size="small"
              dataSource={csvDetect.suggested_mappings}
              pagination={false}
              style={{ marginTop: 8 }}
              columns={[
                {
                  title: "CSV Column",
                  dataIndex: "csv_column",
                  key: "csv_col",
                  render: (col: string) => {
                    const sample = csvDetect.sample_rows[0]?.[col];
                    return (
                      <div>
                        <div><strong>{col}</strong></div>
                        {sample && <Text type="secondary" style={{ fontSize: 12 }}>e.g. {sample}</Text>}
                      </div>
                    );
                  },
                },
                {
                  title: "Maps To",
                  key: "mapped_to",
                  render: (_: any, row: ColumnMapping) => (
                    <Select
                      style={{ width: 220 }}
                      value={csvMappings[row.csv_column] ?? undefined}
                      allowClear
                      placeholder="Ignore this column"
                      onChange={(val) => {
                        setCsvMappings((prev) => ({ ...prev, [row.csv_column]: val || null }));
                      }}
                      options={[
                        ...csvDetect.available_fields.map((f) => ({
                          value: f.field,
                          label: `${f.field}${f.required ? " *" : ""}`,
                          disabled: Object.entries(csvMappings).some(
                            ([k, v]) => v === f.field && k !== row.csv_column,
                          ),
                        })),
                      ]}
                    />
                  ),
                },
                {
                  title: "Description",
                  key: "desc",
                  render: (_: any, row: ColumnMapping) => {
                    const field = csvDetect.available_fields.find(
                      (f) => f.field === csvMappings[row.csv_column],
                    );
                    return field ? <Text type="secondary">{field.description}</Text> : "\u2014";
                  },
                },
              ]}
            />
          </>
        )}

        {csvStep === 2 && csvPreview && (
          <>
            {/* Mapping summary */}
            {csvPreview.column_mappings && csvPreview.column_mappings.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Text type="secondary">
                  Column mapping:{" "}
                  {csvPreview.column_mappings
                    .filter((m) => m.mapped_to)
                    .map((m) => `${m.csv_column} \u2192 ${m.mapped_to}`)
                    .join(", ")}
                </Text>
              </div>
            )}

            {csvPreview.errors.length > 0 && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 12 }}
                message={`${csvPreview.errors.length} warning(s)`}
                description={
                  <ul style={{ margin: 0, paddingLeft: 20 }}>
                    {csvPreview.errors.slice(0, 10).map((e, i) => <li key={i}>{e}</li>)}
                    {csvPreview.errors.length > 10 && <li>...and {csvPreview.errors.length - 10} more</li>}
                  </ul>
                }
              />
            )}

            <p>
              <strong>{csvPreview.new_rows.length}</strong> new rows will be inserted.
              {csvPreview.conflicts.length > 0 && (
                <> <strong>{csvPreview.conflicts.length}</strong> conflict(s) found &mdash; check rows below to overwrite.</>
              )}
            </p>

            <Table
              rowKey="_key"
              size="small"
              dataSource={previewTableData}
              pagination={{ pageSize: 50 }}
              scroll={{ x: 900 }}
              columns={[
                {
                  title: "Row", dataIndex: "row_number", key: "row", width: 60,
                  render: (v: number) => v ?? "\u2014",
                },
                { title: "Parent SKU", dataIndex: "parent_sku", key: "parent_sku" },
                { title: "Child SKU", dataIndex: "child_sku", key: "child_sku" },
                { title: "Qty", dataIndex: "quantity", key: "qty", width: 70 },
                { title: "UOM", dataIndex: "unit_of_measure", key: "uom", width: 60, render: (v: string) => v || "\u2014" },
                { title: "Ref Des", dataIndex: "ref_designator", key: "refdes", render: (v: string) => v || "\u2014" },
                { title: "Line Des", dataIndex: "line_designator", key: "linedes", render: (v: string) => v || "\u2014" },
                { title: "Type", dataIndex: "component_type", key: "type", render: (v: string) => v || "\u2014" },
                { title: "Notes", dataIndex: "notes", key: "notes", ellipsis: true, render: (v: string) => v || "\u2014" },
                {
                  title: "Status", key: "status", width: 120,
                  render: (_: any, r: any) => {
                    if (r._status === "new") return <Tag color="green">New</Tag>;
                    if (r._status === "conflict") {
                      const key = `${r.parent_sku}|||${r.child_sku}`;
                      return (
                        <Space>
                          <Tag color="orange">Conflict</Tag>
                          <Checkbox
                            checked={selectedConflicts.has(key)}
                            onChange={(e) => {
                              setSelectedConflicts((prev) => {
                                const next = new Set(prev);
                                if (e.target.checked) next.add(key);
                                else next.delete(key);
                                return next;
                              });
                            }}
                          >
                            Overwrite
                          </Checkbox>
                        </Space>
                      );
                    }
                    return null;
                  },
                },
              ]}
            />
          </>
        )}
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
              options={otherProducts.map((p) => ({ value: p.id, label: `${p.sku} \u2014 ${p.name}` }))} />
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
              { title: "Notes", dataIndex: "notes", key: "notes", render: (v: string) => v || "\u2014" },
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
