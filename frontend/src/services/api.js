import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Assuming backend runs on 8000

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const loginWithEmail = async (email) => {
    const response = await api.post('/auth/email', { email });
    return response.data;
};

export const loginWithGoogle = async (token) => {
    // In a real app, 'token' would be from Google OAuth
    // Here we'll pass a mock provider and token
    const response = await api.post('/auth/login', {
        provider: 'google',
        access_token: token || 'mock-google-token'
    });
    return response.data;
};

export const uploadGardenPhotos = async (photos, gardenName, userId) => {
    const formData = new FormData();
    photos.forEach((photo) => {
        formData.append('photos', photo);
    });
    if (gardenName) formData.append('garden_name', gardenName);
    if (userId) formData.append('user_id', userId);

    const response = await api.post('/gardens/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const getWorkflowStatus = async (updateId) => {
    const response = await api.get(`/updates/${updateId}/status`);
    return response.data;
};

export const getGardenDetails = async (gardenId) => {
    const response = await api.get(`/gardens/${gardenId}/details`);
    return response.data;
};

export const getUserGardens = async (userId) => {
    const response = await api.get(`/users/${userId}/gardens`);
    return response.data;
};

export const generateGardenVisualization = async (gardenId) => {
    const response = await api.post(`/gardens/${gardenId}/visualize`);
    return response.data;
};


export default api;
