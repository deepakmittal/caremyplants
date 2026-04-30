import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import App from '../App';

// Mock the API and Fonts to avoid asynchronous fetch issues during basic render test
jest.mock('../src/services/api', () => ({
  getDetailedGardens: jest.fn(() => Promise.resolve([]))
}));

jest.mock('expo', () => ({}));

jest.mock('@expo-google-fonts/plus-jakarta-sans', () => ({
  PlusJakartaSans_400Regular: 'PlusJakartaSans_400Regular',
  PlusJakartaSans_600SemiBold: 'PlusJakartaSans_600SemiBold',
  PlusJakartaSans_700Bold: 'PlusJakartaSans_700Bold'
}));

jest.mock('expo-font', () => ({
  useFonts: () => [true] // Mock fonts as loaded
}));

// Mock lucide icons to avoid rendering issues with SVGs in tests
jest.mock('lucide-react-native', () => ({
  Leaf: 'Leaf',
  ChevronRight: 'ChevronRight',
  ArrowLeft: 'ArrowLeft',
  Droplets: 'Droplets',
  Sun: 'Sun'
}));

describe('<App />', () => {
  it('renders the main application header successfully', async () => {
    const { getByText } = render(<App />);
    
    await waitFor(() => {
      expect(getByText('BOTANICAL MANAGER')).toBeTruthy();
      expect(getByText('My Sanctuaries')).toBeTruthy();
    });
  });
});
