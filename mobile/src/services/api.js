import axios from 'axios';
import { Platform } from 'react-native';

// Local Development vs Production backend URL selection
const API_URL = Platform.OS === 'web'
    ? (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8002')
    : 'https://caremyplants-1059916488233.us-central1.run.app';


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
    const isWeb = Platform.OS === 'web';

    if (isWeb) {
        for (const photo of photos) {
            if (photo.file) {
                formData.append('photos', photo.file);
            } else {
                try {
                    const response = await fetch(photo.uri);
                    const blob = await response.blob();
                    formData.append('photos', blob, photo.fileName || `photo_${Date.now()}.jpg`);
                } catch (fetchError) {
                    console.error("Failed to fetch photo uri:", photo.uri, fetchError);
                    throw new Error(`Failed to process selected image: ${fetchError.message}`);
                }
            }
        }
    } else {
        photos.forEach((photo) => {
            const fileData = {
                uri: Platform.OS === 'ios' ? photo.uri.replace('file://', '') : photo.uri,
                type: 'image/jpeg',
                name: photo.fileName || `photo_${Date.now()}.jpg`,
            };
            formData.append('photos', fileData);
        });
    }
    if (gardenName) formData.append('garden_name', gardenName);
    if (userId) formData.append('user_id', userId);
    if (location) formData.append('location', location);

    try {
        const config = {};
        if (!isWeb) {
            config.headers = {
                'Content-Type': 'multipart/form-data',
            };
        }
        const response = await api.post('/gardens/upload', formData, config);
        return response.data;
    } catch (error) {
        console.error('Error uploading garden photos:', error);
        throw error;
    }
};

export const uploadPlantPhoto = async (plantId, photo) => {
    const formData = new FormData();
    const isWeb = Platform.OS === 'web';

    if (isWeb) {
        if (photo.file) {
            formData.append('photo', photo.file);
        } else {
            const response = await fetch(photo.uri);
            const blob = await response.blob();
            formData.append('photo', blob, photo.fileName || `photo_${Date.now()}.jpg`);
        }
    } else {
        const fileData = {
            uri: Platform.OS === 'ios' ? photo.uri.replace('file://', '') : photo.uri,
            type: 'image/jpeg',
            name: photo.fileName || `photo_${Date.now()}.jpg`,
        };
        formData.append('photo', fileData);
    }

    try {
        const config = {};
        if (!isWeb) {
            config.headers = {
                'Content-Type': 'multipart/form-data',
            };
        }
        const response = await api.post(`/plants/${plantId}/photos`, formData, config);
        return response.data;
    } catch (error) {
        console.error('Error uploading plant photo:', error);
        throw error;
    }
};

export const getPlantUpdates = async (plantId) => {
    try {
        const response = await api.get(`/plants/${plantId}/updates`);
        return response.data;
    } catch (error) {
        console.error('Error fetching plant updates:', error);
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

export const getDbStatus = async () => {
    try {
        const response = await api.get('/db/status');
        return response.data;
    } catch (error) {
        console.error('Error checking DB status:', error);
        throw error;
    }
};

export const startDb = async () => {
    try {
        const response = await api.post('/db/start');
        return response.data;
    } catch (error) {
        console.error('Error starting DB:', error);
        throw error;
    }
};

export default api;
