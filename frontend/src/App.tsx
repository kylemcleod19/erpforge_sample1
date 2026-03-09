import {
  AppstoreOutlined,
  AuditOutlined,
  BarChartOutlined,
  CarOutlined,
  ContainerOutlined,
  FileTextOutlined,
  PartitionOutlined,
  ShoppingCartOutlined,
  ShoppingOutlined,
  ToolOutlined,
} from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import React, { useState } from "react";
import { Link, BrowserRouter as Router, Route, Routes, useLocation } from "react-router-dom";
import Inventory from "./pages/Inventory";
import Invoices from "./pages/Invoices";
import OrderDetail from "./pages/OrderDetail";
import Orders from "./pages/Orders";
import ProductDetail from "./pages/ProductDetail";
import Products from "./pages/Products";
import Purchasing from "./pages/Purchasing";
import QuoteDetail from "./pages/QuoteDetail";
import Quotes from "./pages/Quotes";
import Shipping from "./pages/Shipping";
import Stations from "./pages/Stations";
import WorkOrders from "./pages/WorkOrders";

const { Header, Sider, Content } = Layout;

const NAV_ITEMS = [
  { key: "/products", icon: <AppstoreOutlined />, label: <Link to="/products">Products</Link> },
  { key: "/quotes", icon: <FileTextOutlined />, label: <Link to="/quotes">Quotes</Link> },
  { key: "/orders", icon: <ShoppingCartOutlined />, label: <Link to="/orders">Orders</Link> },
  { key: "/work-orders", icon: <ToolOutlined />, label: <Link to="/work-orders">Work Orders</Link> },
  { key: "/stations", icon: <PartitionOutlined />, label: <Link to="/stations">Stations & Routing</Link> },
  { key: "/inventory", icon: <ContainerOutlined />, label: <Link to="/inventory">Inventory</Link> },
  { key: "/purchasing", icon: <ShoppingOutlined />, label: <Link to="/purchasing">Purchasing</Link> },
  { key: "/shipping", icon: <CarOutlined />, label: <Link to="/shipping">Shipping</Link> },
  { key: "/invoices", icon: <AuditOutlined />, label: <Link to="/invoices">Invoices</Link> },
];

function AppLayout() {
  const location = useLocation();
  const selectedKey = "/" + location.pathname.split("/")[1];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={220} theme="dark" style={{ position: "fixed", height: "100vh", overflow: "auto" }}>
        <div style={{ padding: "16px", textAlign: "center" }}>
          <Typography.Text strong style={{ color: "#fff", fontSize: 18 }}>
            ERPForge
          </Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={NAV_ITEMS}
        />
      </Sider>
      <Layout style={{ marginLeft: 220 }}>
        <Content style={{ padding: "24px", minHeight: "calc(100vh - 64px)" }}>
          <Routes>
            <Route path="/" element={<Products />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/quotes" element={<Quotes />} />
            <Route path="/quotes/:id" element={<QuoteDetail />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/orders/:id" element={<OrderDetail />} />
            <Route path="/work-orders" element={<WorkOrders />} />
            <Route path="/stations" element={<Stations />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/purchasing" element={<Purchasing />} />
            <Route path="/shipping" element={<Shipping />} />
            <Route path="/invoices" element={<Invoices />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}
