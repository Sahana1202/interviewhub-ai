import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api'),
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

api.interceptors.response.use((response) => response, (error) => {
  const route = error.config?.url ?? '';
  if (error.response?.status === 401 && !route.endsWith('/auth/login') && !route.endsWith('/auth/register')) {
    localStorage.removeItem('interviewhub_access_token');
    window.dispatchEvent(new Event('interviewhub:unauthorized'));
  }
  return Promise.reject(error);
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('interviewhub_access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

function messageFromError(error) {
  if (!error.response) return 'The service is unavailable. Check the backend and your connection, then try again.';
  if (error.response.status === 401) return 'Your session has expired. Please log in again.';
  const detail = error.response.data?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ');
  if (error.response.status >= 500) return 'Something went wrong. Please try again.';
  return typeof detail === 'string' ? detail : 'The request could not be completed. Please try again.';
}

export const authApi = {
  async register(payload) {
    try { return (await api.post('/auth/register', payload)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async login(payload) {
    try { return (await api.post('/auth/login', payload)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async me() {
    try { return (await api.get('/auth/me')).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
};

export const profileApi = {
  async get() {
    try { return (await api.get('/profile')).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async update(payload) {
    try { return (await api.put('/profile', payload)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async completeOnboarding(payload) {
    try { return (await api.post('/profile/onboarding', payload)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
};
export const dashboardApi = {
  async get() {
    try { return (await api.get('/dashboard')).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
};
export const interviewApi = {
  async aiStatus() { try { return (await api.get('/ai/status')).data; } catch { return { available: false, provider: null, model: null }; } },
  async aiQuestion(id) { try { return (await api.post(`/interviews/${id}/ai/question`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async evaluate(id, answerId) { try { return (await api.post(`/interviews/${id}/answers/${answerId}/evaluate`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async followup(id, answerId) { try { return (await api.post(`/interviews/${id}/follow-up`, null, { params: { answer_id: answerId } })).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async finalEvaluation(id) { try { return (await api.post(`/interviews/${id}/final-evaluation`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async report(id) { try { return (await api.get(`/interviews/${id}/report`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async interviewers() {
    try { return (await api.get('/interviews/interviewers')).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async start(payload) {
    try { return (await api.post('/interviews/start', payload)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async list() {
    try { return (await api.get('/interviews')).data.sessions; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async get(id) {
    try { return (await api.get(`/interviews/${id}`)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async answer(id, payload) {
    try { return (await api.post(`/interviews/${id}/answer`, payload)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async pause(id) {
    try { return (await api.post(`/interviews/${id}/pause`)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async complete(id) {
    try { return (await api.post(`/interviews/${id}/complete`)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
};
export const resumeApi = {
  async list() {
    try { return (await api.get('/resumes')).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async get(id) {
    try { return (await api.get(`/resumes/${id}`)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async upload(file, onUploadProgress) {
    const form = new FormData(); form.append('file', file);
    try { return (await api.post('/resumes/upload', form, { headers: { 'Content-Type': 'multipart/form-data' }, onUploadProgress })).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async analyze(id) {
    try { return (await api.post(`/resumes/${id}/analyze`)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async delete(id) {
    try { await api.delete(`/resumes/${id}`); }
    catch (error) { throw new Error(messageFromError(error)); }
  },
  async interviewContext(id) {
    try { return (await api.get(`/resumes/${id}/interview-context`)).data; }
    catch (error) { throw new Error(messageFromError(error)); }
  },
};
export const jobMatchApi = {};
export const companyApi = {
  async list(q = '') { try { return (await api.get('/companies', { params: q ? { q } : {} })).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async bookmarks() { try { return (await api.get('/companies/bookmarks')).data.companies; } catch (error) { throw new Error(messageFromError(error)); } },
  async get(id) { try { return (await api.get(`/companies/${id}`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async bookmark(id) { try { await api.post(`/companies/${id}/bookmark`); } catch (error) { throw new Error(messageFromError(error)); } },
  async unbookmark(id) { try { await api.delete(`/companies/${id}/bookmark`); } catch (error) { throw new Error(messageFromError(error)); } },
  async quiz(id) { try { return (await api.get(`/companies/${id}/quiz`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async answer(id, payload) { try { return (await api.post(`/companies/${id}/quiz/answer`, payload)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async context(id) { try { return (await api.get(`/companies/${id}/interview-context`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
};
export const learningApi = {
  async categories() { try { return (await api.get('/learning/categories')).data.categories; } catch (error) { throw new Error(messageFromError(error)); } },
  async category(id) { try { return (await api.get(`/learning/categories/${id}`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async topics(params = {}) { try { return (await api.get('/learning/topics', { params })).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async topic(id) { try { return (await api.get(`/learning/topics/${id}`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async completeTopic(id) { try { return (await api.post(`/learning/topics/${id}/complete`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async progress() { try { return (await api.get('/learning/progress')).data.progress; } catch (error) { throw new Error(messageFromError(error)); } },
  async recommendations() { try { return (await api.get('/learning/recommendations')).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async resources(params = {}) { try { return (await api.get('/resources', { params })).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async resource(id) { try { return (await api.get(`/resources/${id}`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
};
export const practiceApi = {
  async start(payload) { try { return (await api.post('/practice/start', payload)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async get(id) { try { return (await api.get(`/practice/${id}`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async answer(id, payload) { try { return (await api.post(`/practice/${id}/answer`, payload)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async complete(id) { try { return (await api.post(`/practice/${id}/complete`)).data; } catch (error) { throw new Error(messageFromError(error)); } },
  async history(params = {}) { try { return (await api.get('/practice/history', { params })).data; } catch (error) { throw new Error(messageFromError(error)); } },
};
export const roadmapApi = {};

export default api;
