import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button, Card, Descriptions, Form, InputNumber, Popconfirm,
  Select, Space, Table, Tag, Typography, message
} from "antd";
import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Product, productsApi } from "../api/products";
import { Quote, QuoteLineItem, quotesApi } from "../api/quotes";

const { Title } = Typography;

const STATUS_COLOR: Record<string, string> = {
  draft: "default", review: "processing", approved: "cyan",
  sent: "orange", won: "green", lost: "red",
};

const TRANSITIONS: Record<string, Array<{ label: string; to: string; danger?: boolean }>> = {
  draft: [{ label: "Submit for Review", to: "review" }, { label: "Mark Lost", to: "lost", danger: true }],
  review: [
    { label: "Approve", to: "approved" },
    { label: "Back to Draft", to: "draft" },
    { label: "Mark Lost", to: "lost", danger: true },
  ],
  approved: [{ label: "Send to Customer", to: "sent" }, { label: "Mark Lost", to: "lost", danger: true }],
  sent: [{ label: "Mark Won", to: "won" }, { label: "Mark Lost", to: "lost", danger: true }],
  won: [],
  lost: [],
};

export default function QuoteDetail() {
  const { id } = useParams<{ id: string }>();
  const qid = parseInt(id!);
  const navigate = useNavigate();

  const [quote, setQuote] = useState<Quote | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [form] = Form.useForm();
  const [converting, setConverting] = useState(false);

  const load = async () => {
    const [q, ps] = await Promise.all([quotesApi.get(qid), productsApi.list()]);
    setQuote(q);
    setProducts(ps);
  };

  useEffect(() => { load(); }, [qid]);

  const transition = async (to: string) => {
    try { await quotesApi.transition(qid, to); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const convert = async () => {
    setConverting(true);
    try {
      const order = await quotesApi.convert(qid) as any;
      message.success(`Order #${order.id} created`);
      navigate(`/orders/${order.id}`);
    } catch (e: any) { message.error(e.message); }
    finally { setConverting(false); }
  };

  const addLine = async () => {
    const vals = await form.validateFields();
    try {
      await quotesApi.addLineItem(qid, vals);
      message.success("Line item added");
      form.resetFields();
      load();
    } catch (e: any) { message.error(e.message); }
  };

  const removeLine = async (itemId: number) => {
    try { await quotesApi.removeLineItem(qid, itemId); load(); }
    catch (e: any) { message.error(e.message); }
  };

  if (!quote) return <div>Loading...</div>;

  const total = quote.line_items.reduce((s, li) => s + Number(li.subtotal), 0);
  const transitions = TRANSITIONS[quote.status] || [];
  const canEdit = !["won", "lost"].includes(quote.status);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>Quote #{quote.id}</Title>
        <Space>
          {transitions.map((t) => (
            <Button key={t.to} danger={t.danger} type={t.danger ? "default" : "primary"} onClick={() => transition(t.to)}>{t.label}</Button>
          ))}
          {quote.status === "won" && (
            <Button type="primary" loading={converting} onClick={convert}>Convert to Order</Button>
          )}
        </Space>
      </div>

      <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="Customer">{quote.customer_name}</Descriptions.Item>
        <Descriptions.Item label="Email">{quote.customer_email || "—"}</Descriptions.Item>
        <Descriptions.Item label="Status"><Tag color={STATUS_COLOR[quote.status]}>{quote.status.toUpperCase()}</Tag></Descriptions.Item>
        <Descriptions.Item label="Created">{new Date(quote.created_at).toLocaleString()}</Descriptions.Item>
        <Descriptions.Item label="Notes" span={2}>{quote.notes || "—"}</Descriptions.Item>
      </Descriptions>

      <Card title="Line Items">
        {canEdit && (
          <Form form={form} layout="inline" style={{ marginBottom: 12 }}>
            <Form.Item name="product_id" label="Product" rules={[{ required: true }]}>
              <Select style={{ width: 200 }} showSearch optionFilterProp="label"
                options={products.map((p) => ({ value: p.id, label: `${p.sku} — ${p.name}` }))} />
            </Form.Item>
            <Form.Item name="quantity" label="Qty" rules={[{ required: true }]}>
              <InputNumber min={0.0001} precision={4} />
            </Form.Item>
            <Form.Item name="unit_price" label="Price" rules={[{ required: true }]}>
              <InputNumber min={0} precision={4} prefix="$" />
            </Form.Item>
            <Form.Item name="lead_time_days" label="Lead Days">
              <InputNumber min={0} />
            </Form.Item>
            <Button type="primary" icon={<PlusOutlined />} onClick={addLine}>Add</Button>
          </Form>
        )}
        <Table
          rowKey="id"
          size="small"
          dataSource={quote.line_items}
          columns={[
            { title: "SKU", dataIndex: "product_sku", key: "sku" },
            { title: "Product", dataIndex: "product_name", key: "name" },
            { title: "Qty", dataIndex: "quantity", key: "qty" },
            { title: "Unit Price", dataIndex: "unit_price", key: "price", render: (v: number) => `$${Number(v).toFixed(2)}` },
            { title: "Lead Days", dataIndex: "lead_time_days", key: "lead" },
            { title: "Subtotal", dataIndex: "subtotal", key: "subtotal", render: (v: number) => `$${Number(v).toFixed(2)}` },
            {
              title: "", key: "del",
              render: (_: any, r: QuoteLineItem) => canEdit ? (
                <Popconfirm title="Remove?" onConfirm={() => removeLine(r.id)}>
                  <Button icon={<DeleteOutlined />} size="small" danger />
                </Popconfirm>
              ) : null,
            },
          ]}
          summary={() => (
            <Table.Summary.Row>
              <Table.Summary.Cell index={0} colSpan={5}><strong>Total</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={5}><strong>${total.toFixed(2)}</strong></Table.Summary.Cell>
              <Table.Summary.Cell index={6} />
            </Table.Summary.Row>
          )}
        />
      </Card>
    </div>
  );
}
