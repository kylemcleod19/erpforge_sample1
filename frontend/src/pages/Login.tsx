import { LockOutlined, MailOutlined, RocketOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Card, Divider, Form, Input, message, Radio, Tabs, Typography } from "antd";
import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

export default function Login() {
  const { login, register, demoLogin } = useAuth();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [submitting, setSubmitting] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleLogin = async (values: { email: string; password: string }) => {
    setSubmitting(true);
    try {
      await login(values.email, values.password);
    } catch (e: any) {
      message.error(e.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegister = async (values: {
    email: string;
    password: string;
    display_name: string;
    role: string;
  }) => {
    setSubmitting(true);
    try {
      await register(values.email, values.password, values.display_name, values.role);
    } catch (e: any) {
      message.error(e.message || "Registration failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setDemoLoading(true);
    try {
      await demoLogin();
    } catch (e: any) {
      message.error(e.message || "Demo login failed");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        background: "#f0f2f5",
      }}
    >
      <Card style={{ width: 420 }}>
        <Typography.Title level={3} style={{ textAlign: "center", marginBottom: 24 }}>
          ERPForge
        </Typography.Title>

        <Tabs
          activeKey={tab}
          onChange={(k) => setTab(k as "login" | "register")}
          centered
          items={[
            {
              key: "login",
              label: "Sign In",
              children: (
                <Form onFinish={handleLogin} layout="vertical">
                  <Form.Item name="email" rules={[{ required: true, type: "email" }]}>
                    <Input prefix={<MailOutlined />} placeholder="Email" size="large" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true }]}>
                    <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={submitting} block size="large">
                    Sign In
                  </Button>
                </Form>
              ),
            },
            {
              key: "register",
              label: "Register",
              children: (
                <Form onFinish={handleRegister} layout="vertical" initialValues={{ role: "sales" }}>
                  <Form.Item name="display_name" rules={[{ required: true, message: "Enter your name" }]}>
                    <Input prefix={<UserOutlined />} placeholder="Display Name" size="large" />
                  </Form.Item>
                  <Form.Item name="email" rules={[{ required: true, type: "email" }]}>
                    <Input prefix={<MailOutlined />} placeholder="Email" size="large" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, min: 6 }]}>
                    <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
                  </Form.Item>
                  <Form.Item name="role" label="Role">
                    <Radio.Group>
                      <Radio.Button value="admin">Admin</Radio.Button>
                      <Radio.Button value="engineer">Engineer</Radio.Button>
                      <Radio.Button value="sales">Sales</Radio.Button>
                    </Radio.Group>
                  </Form.Item>
                  <Button type="primary" htmlType="submit" loading={submitting} block size="large">
                    Create Account
                  </Button>
                </Form>
              ),
            },
          ]}
        />
      </Card>
      <Divider style={{ width: 420, minWidth: 420, margin: "16px 0 0" }}>or</Divider>
      <Button
        icon={<RocketOutlined />}
        size="large"
        loading={demoLoading}
        onClick={handleDemoLogin}
        style={{ marginTop: 8, width: 420 }}
      >
        Try Demo
      </Button>
      <Typography.Text type="secondary" style={{ marginTop: 8, fontSize: 12 }}>
        Explore with a pre-loaded admin account and sample data
      </Typography.Text>
    </div>
  );
}
