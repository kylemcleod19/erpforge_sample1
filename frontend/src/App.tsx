import {
  AppstoreOutlined,
  AuditOutlined,
  BlockOutlined,
  CarOutlined,
  ContainerOutlined,
  FileTextOutlined,
  LogoutOutlined,
  PartitionOutlined,
  ShoppingCartOutlined,
  ShoppingOutlined,
  ToolOutlined,
} from "@ant-design/icons";
import { Button, Layout, Menu, Spin, Tag, Typography } from "antd";
import React, { useCallback, useState } from "react";
import { Link, BrowserRouter as Router, Route, Routes, useLocation } from "react-router-dom";
import CopilotWidget from "./components/CopilotWidget";
import OnboardingChecklist from "./components/OnboardingChecklist";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Inventory from "./pages/Inventory";
import Invoices from "./pages/Invoices";
import Login from "./pages/Login";
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

const { Sider, Content } = Layout;

const NAV_ITEMS = [
  { key: "/products", icon: <AppstoreOutlined />, label: <Link to="/products">Products</Link> },
  { key: "/components", icon: <BlockOutlined />, label: <Link to="/components">Components</Link> },
  { key: "/quotes", icon: <FileTextOutlined />, label: <Link to="/quotes">Quotes</Link> },
  { key: "/orders", icon: <ShoppingCartOutlined />, label: <Link to="/orders">Orders</Link> },
  { key: "/work-orders", icon: <ToolOutlined />, label: <Link to="/work-orders">Work Orders</Link> },
  { key: "/stations", icon: <PartitionOutlined />, label: <Link to="/stations">Stations & Routing</Link> },
  { key: "/inventory", icon: <ContainerOutlined />, label: <Link to="/inventory">Inventory</Link> },
  { key: "/purchasing", icon: <ShoppingOutlined />, label: <Link to="/purchasing">Purchasing</Link> },
  { key: "/shipping", icon: <CarOutlined />, label: <Link to="/shipping">Shipping</Link> },
  { key: "/invoices", icon: <AuditOutlined />, label: <Link to="/invoices">Invoices</Link> },
];

const ROLE_COLORS: Record<string, string> = {
  admin: "red",
  engineer: "blue",
  sales: "green",
};

function AppLayout() {
  const location = useLocation();
  const selectedKey = "/" + location.pathname.split("/")[1];
  const { user, logout } = useAuth();
  const [copilotPrompt, setCopilotPrompt] = useState<string | null>(null);

  const handleMilestoneClick = useCallback((prompt: string) => {
    setCopilotPrompt(prompt);
  }, []);

  const handlePromptConsumed = useCallback(() => {
    setCopilotPrompt(null);
  }, []);

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
        <OnboardingChecklist onMilestoneClick={handleMilestoneClick} />
        {user && (
          <div style={{ position: "absolute", bottom: 0, width: "100%", padding: "16px" }}>
            <div style={{ color: "#fff", marginBottom: 8, fontSize: 13 }}>
              {user.display_name}
              <Tag color={ROLE_COLORS[user.role] || "default"} style={{ marginLeft: 8 }}>
                {user.role}
              </Tag>
            </div>
            <Button
              icon={<LogoutOutlined />}
              size="small"
              type="text"
              style={{ color: "#aaa" }}
              onClick={logout}
            >
              Sign out
            </Button>
          </div>
        )}
      </Sider>
      <Layout style={{ marginLeft: 220 }}>
        <Content style={{ padding: "24px", minHeight: "calc(100vh - 64px)" }}>
          <Routes>
            <Route path="/" element={<Products itemTypes={["finished_good", "assembly"]} pageTitle="Products" />} />
            <Route path="/products" element={<Products itemTypes={["finished_good", "assembly"]} pageTitle="Products" />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/components" element={<Products itemTypes={["component", "raw_material"]} pageTitle="Components" />} />
            <Route path="/components/:id" element={<ProductDetail />} />
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
      <CopilotWidget
        initialPrompt={copilotPrompt}
        onPromptConsumed={handlePromptConsumed}
      />
    </Layout>
  );
}

function AuthGate() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <Spin size="large" />
      </div>
    );
  }

  return isAuthenticated ? <AppLayout /> : <Login />;
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AuthGate />
      </AuthProvider>
    </Router>
  );
}
