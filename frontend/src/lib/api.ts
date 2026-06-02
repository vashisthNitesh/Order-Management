import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

// Attach JWT token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const { data } = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          localStorage.setItem("access_token", data.access);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access}`;
          }
          return api(originalRequest);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/staff/login";
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: (username: string, password: string) =>
    api.post("/auth/login/", { username, password }),
  logout: (refresh: string) => api.post("/auth/logout/", { refresh }),
  profile: () => api.get("/auth/profile/"),
};

// Restaurants
export const restaurantApi = {
  list: () => api.get("/restaurants/"),
  get: (id: number) => api.get(`/restaurants/${id}/`),
  update: (id: number, data: FormData | object) =>
    api.patch(`/restaurants/${id}/`, data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
};

// Tables
export const tableApi = {
  list: (restaurantId?: number) =>
    api.get("/restaurants/tables/", { params: restaurantId ? { restaurant: restaurantId } : {} }),
  get: (id: number) => api.get(`/restaurants/tables/${id}/`),
  create: (data: object) => api.post("/restaurants/tables/", data),
  update: (id: number, data: object) => api.patch(`/restaurants/tables/${id}/`, data),
  delete: (id: number) => api.delete(`/restaurants/tables/${id}/`),
  regenerateQr: (id: number, baseUrl: string) =>
    api.post(`/restaurants/tables/${id}/regenerate_qr/`, { base_url: baseUrl }),
};

// Categories
export const categoryApi = {
  list: (restaurantId?: number) =>
    api.get("/menu/categories/", { params: restaurantId ? { restaurant: restaurantId } : {} }),
  get: (id: number) => api.get(`/menu/categories/${id}/`),
  create: (data: FormData | object) =>
    api.post("/menu/categories/", data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
  update: (id: number, data: FormData | object) =>
    api.patch(`/menu/categories/${id}/`, data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
  delete: (id: number) => api.delete(`/menu/categories/${id}/`),
};

// Menu Items
export const menuItemApi = {
  list: (params?: object) => api.get("/menu/items/", { params }),
  get: (id: number) => api.get(`/menu/items/${id}/`),
  popular: (restaurantId?: number) =>
    api.get("/menu/items/popular/", { params: restaurantId ? { restaurant: restaurantId } : {} }),
  specials: (restaurantId?: number) =>
    api.get("/menu/items/specials/", { params: restaurantId ? { restaurant: restaurantId } : {} }),
  create: (data: FormData | object) =>
    api.post("/menu/items/", data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
  update: (id: number, data: FormData | object) =>
    api.patch(`/menu/items/${id}/`, data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
  delete: (id: number) => api.delete(`/menu/items/${id}/`),
};

// Orders
export const orderApi = {
  list: (params?: object) => api.get("/orders/", { params }),
  get: (id: number) => api.get(`/orders/${id}/`),
  create: (data: object) => api.post("/orders/", data),
  updateStatus: (id: number, status: string) =>
    api.patch(`/orders/${id}/update_status/`, { status }),
  dashboardStats: (restaurantId?: number) =>
    api.get("/orders/dashboard_stats/", { params: restaurantId ? { restaurant: restaurantId } : {} }),
};

// Offers
export const offerApi = {
  list: (params?: object) => api.get("/offers/", { params }),
  get: (id: number) => api.get(`/offers/${id}/`),
  create: (data: FormData | object) =>
    api.post("/offers/", data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
  update: (id: number, data: FormData | object) =>
    api.patch(`/offers/${id}/`, data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : {},
    }),
  delete: (id: number) => api.delete(`/offers/${id}/`),
};

// Staff
export const staffApi = {
  list: (params?: object) => api.get("/staff/", { params }),
  get: (id: number) => api.get(`/staff/${id}/`),
  create: (data: object) => api.post("/staff/", data),
  update: (id: number, data: object) => api.patch(`/staff/${id}/`, data),
  delete: (id: number) => api.delete(`/staff/${id}/`),
};

export default api;
