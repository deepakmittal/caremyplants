import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
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

export default api;
