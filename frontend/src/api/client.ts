import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.detail || err.message || "An error occurred";
    console.error("API Error:", msg);
    return Promise.reject(new Error(typeof msg === "string" ? msg : JSON.stringify(msg)));
  }
);

export default client;
