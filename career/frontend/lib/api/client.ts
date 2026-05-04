import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { apiLogger } from '../logger';

// API base URLs for each service
const API_URLS = {
  auth: process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:8011',
  student: process.env.NEXT_PUBLIC_STUDENT_API_URL || 'http://localhost:8002',
  competency: process.env.NEXT_PUBLIC_COMPETENCY_API_URL || 'http://localhost:8003',
  alumni: process.env.NEXT_PUBLIC_ALUMNI_API_URL || 'http://localhost:8005',
  integration: process.env.NEXT_PUBLIC_INTEGRATION_API_URL || 'http://localhost:8019',
  // P1 Services
  skill: process.env.NEXT_PUBLIC_SKILL_API_URL || 'http://localhost:8007',
  opportunity: process.env.NEXT_PUBLIC_OPPORTUNITY_API_URL || 'http://localhost:8008',
  coaching: process.env.NEXT_PUBLIC_COACHING_API_URL || 'http://localhost:8009',
  risk: process.env.NEXT_PUBLIC_RISK_API_URL || 'http://localhost:8010',
  // P2 Services
  badge: process.env.NEXT_PUBLIC_BADGE_API_URL || 'http://localhost:8012',
  simulation: process.env.NEXT_PUBLIC_SIMULATION_API_URL || 'http://localhost:8013',
  advisor: process.env.NEXT_PUBLIC_ADVISOR_API_URL || 'http://localhost:8014',
  roadmap: process.env.NEXT_PUBLIC_ROADMAP_API_URL || 'http://localhost:8015',
  portfolio: process.env.NEXT_PUBLIC_PORTFOLIO_API_URL || 'http://localhost:8016',
};

// Create axios instances for each service
export const authApi = axios.create({
  baseURL: API_URLS.auth,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const studentApi = axios.create({
  baseURL: API_URLS.student,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const competencyApi = axios.create({
  baseURL: API_URLS.competency,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const alumniApi = axios.create({
  baseURL: API_URLS.alumni,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const integrationApi = axios.create({
  baseURL: API_URLS.integration,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// P1 Services
export const skillApi = axios.create({
  baseURL: API_URLS.skill,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const opportunityApi = axios.create({
  baseURL: API_URLS.opportunity,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const coachingApi = axios.create({
  baseURL: API_URLS.coaching,
  timeout: 30000, // Longer timeout for AI responses
  headers: {
    'Content-Type': 'application/json',
  },
});

export const riskApi = axios.create({
  baseURL: API_URLS.risk,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// P2 Services
export const badgeApi = axios.create({
  baseURL: API_URLS.badge,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const simulationApi = axios.create({
  baseURL: API_URLS.simulation,
  timeout: 30000, // Longer timeout for simulations
  headers: {
    'Content-Type': 'application/json',
  },
});

export const advisorApi = axios.create({
  baseURL: API_URLS.advisor,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const roadmapApi = axios.create({
  baseURL: API_URLS.roadmap,
  timeout: 30000, // Longer timeout for AI generation
  headers: {
    'Content-Type': 'application/json',
  },
});

export const portfolioApi = axios.create({
  baseURL: API_URLS.portfolio,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generic API client (for ai-service and other services that specify full URLs)
export const apiClient = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Internal network support: resolve localhost to actual browser hostname
const resolveNetworkHost = (config: InternalAxiosRequestConfig) => {
  if (typeof window !== 'undefined' && config.baseURL) {
    const hostname = window.location.hostname;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      config.baseURL = config.baseURL.replace('//localhost:', `//${hostname}:`);
    }
  }
  return config;
};

// Request interceptor for logging
const logRequest = (config: InternalAxiosRequestConfig) => {
  apiLogger.debug(`${config.method?.toUpperCase()} ${config.url}`, {
    baseURL: config.baseURL,
    params: config.params,
  });
  return config;
};

// Response interceptor for logging
const logResponse = (response: AxiosResponse) => {
  apiLogger.debug(`Response ${response.status} ${response.config.url}`, {
    status: response.status,
    dataSize: JSON.stringify(response.data).length,
  });
  return response;
};

// Error handler with logging
const handleApiError = (error: AxiosError) => {
  const url = error.config?.url || 'unknown';
  const method = error.config?.method?.toUpperCase() || 'UNKNOWN';

  if (error.response) {
    const detail = (error.response.data as { detail?: string })?.detail;
    apiLogger.error(`API Error: ${method} ${url}`, error, {
      status: error.response.status,
      data: error.response.data,
    });
    throw new Error(detail || 'API request failed');
  } else if (error.request) {
    apiLogger.error(`Network Error: ${method} ${url}`, error, {
      message: error.message,
    });
    throw new Error('Network error - please check if the backend services are running');
  } else {
    apiLogger.error(`Request Error: ${method} ${url}`, error);
    throw error;
  }
};

// Add interceptors to all API instances
[
  authApi, studentApi, competencyApi, alumniApi, integrationApi,
  skillApi, opportunityApi, coachingApi, riskApi,
  badgeApi, simulationApi, advisorApi, roadmapApi, portfolioApi,
  apiClient
].forEach(api => {
  api.interceptors.request.use(resolveNetworkHost);
  api.interceptors.request.use(logRequest);
  api.interceptors.response.use(logResponse, handleApiError);
});

export { API_URLS };
