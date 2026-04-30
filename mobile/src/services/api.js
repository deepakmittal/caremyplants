import axios from 'axios';
import { Platform } from 'react-native';

// Note: When running on a real device on Wi-Fi, use your machine's local IP address (e.g., 192.168.1.x)
// For Android Emulators, 10.0.2.2 automatically routes to the host computer's localhost
const API_URL = 'http://192.168.1.4:8000'; // Machine local IP for emulator/device connectivity


const api = axios.create({
    baseURL: API_URL,
});

export const getDetailedGardens = async (userId) => {
    try {
        const response = await api.get(`/users/${userId}/gardens/detailed`);
        return response.data;
    } catch (error) {
        console.error('Error fetching detailed gardens:', error);
        throw error;
    }
};

export const uploadGardenPhotos = async (photos, gardenName, userId, location) => {
    const formData = new FormData();
    photos.forEach((photo) => {
        const fileData = {
            uri: Platform.OS === 'ios' ? photo.uri.replace('file://', '') : photo.uri,
            type: 'image/jpeg',
            name: photo.fileName || `photo_${Date.now()}.jpg`,
        };
        formData.append('photos', fileData);
    });
    if (gardenName) formData.append('garden_name', gardenName);
    if (userId) formData.append('user_id', userId);
    if (location) formData.append('location', location);

    try {
        const response = await api.post('/gardens/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        console.error('Error uploading garden photos:', error);
        throw error;
    }
};

export const updateGardenAccess = async (gardenId) => {
    try {
        const response = await api.put(`/gardens/${gardenId}/access`);
        return response.data;
    } catch (error) {
        console.error('Error updating garden access:', error);
        throw error;
    }
};

export const getGardenEnvironment = async (gardenId) => {
    try {
        const response = await api.get(`/gardens/${gardenId}/environment`);
        return response.data;
    } catch (error) {
        console.error('Error fetching garden environment:', error);
        throw error;
    }
};

export const deleteGarden = async (gardenId) => {
    try {
        const response = await api.delete(`/gardens/${gardenId}`);
        return response.data;
    } catch (error) {
        console.error('Error deleting garden:', error);
        throw error;
    }
};

export default api;
