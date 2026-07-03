
import React, { useEffect, useState, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  Image,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
  StatusBar,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
  Alert,
  Modal
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { theme } from './src/theme';
import { getDetailedGardens, uploadGardenPhotos, deleteGarden } from './src/services/api';
import { 
  Leaf, ChevronRight, ArrowLeft, Droplets, Sun, Plus, Image as ImageIcon, Sparkles, MapPin, Trash2,
  CheckCircle2, HeartPulse, Sprout, Wind, Archive, Scissors 
} from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import * as Font from 'expo-font';
import { Manrope_400Regular, Manrope_600SemiBold, Manrope_700Bold } from '@expo-google-fonts/manrope';
import PlantDetails from './src/components/PlantDetails';
import Svg, { Circle } from 'react-native-svg';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width * 0.85;

// --- NEW COMPONENTS START ---

const SanctuaryVitalityCard = ({ vitality }) => {
  if (!vitality) return null;

  const score = vitality.score || 0;
  const size = 80;
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const progress = score / 100;
  const strokeDashoffset = circumference * (1 - progress);

  const strokeColor = score > 90 ? theme.colors.primaryContainer : theme.colors.vibrantPink;

  return (
    <View style={styles.vitalityCard}>
      <View style={styles.vitalityContent}>
        <Text style={styles.vitalityLabel}>SANCTUARY VITALITY</Text>
        <Text style={styles.vitalityScore}>{score}%</Text>
        <Text style={styles.vitalitySummary}>
          {vitality.flourishingPlantsCount} plants are flourishing, {vitality.careNeededPlantsCount} need care.
        </Text>
      </View>
      <View style={styles.vitalityChart}>
        <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <Circle
            stroke={theme.colors.outlineVariant}
            opacity={0.3}
            fill="none"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={strokeWidth}
          />
          <Circle
            stroke={strokeColor}
            fill="none"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size/2} ${size/2})`}
          />
        </Svg>
        <View style={styles.vitalityChartIcon}>
          <Leaf size={24} color={strokeColor} />
        </View>
      </View>
    </View>
  );
};

const MetricTile = ({ metric, onPress }) => {
  const METRIC_ICONS = {
    WATERING: Droplets,
    SUN_EXPOSURE: Sun,
    SOIL_QUALITY: Sprout,
    VITALITY: HeartPulse,
    LEAF_CARE: Wind,
    POT_STATUS: Archive,
    PRUNING: Scissors,
  };

  const Icon = METRIC_ICONS[metric.category] || Leaf;

  return (
    <TouchableOpacity style={styles.metricTile} activeOpacity={0.8} onPress={() => onPress(metric)}>
      {metric.isUnfavorable && (
        <View style={styles.metricBadge}>
          <Text style={styles.metricBadgeText}>{metric.affectedPlantsCount}</Text>
        </View>
      )}
      <View style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'center'}}>
        <Icon size={28} color={metric.isUnfavorable ? theme.colors.vibrantPink : theme.colors.primary} />
        {!metric.isUnfavorable && <CheckCircle2 size={16} color="green" style={{ marginLeft: 4 }} />}
      </View>
      <View>
        <Text style={styles.metricLabel}>{metric.category.replace('_', ' ')}</Text>
        <Text style={[styles.metricStatus, metric.isUnfavorable ? { color: theme.colors.vibrantPink } : { color: theme.colors.primary }]}>{metric.status}</Text>
      </View>
    </TouchableOpacity>
  );
};

const MetricTileGrid = ({ metrics, onMetricPress }) => {
  if (!metrics || metrics.length === 0) return null;
  return (
    <View style={styles.metricGrid}>
      {metrics.map((metric) => (
        <MetricTile key={metric.category} metric={metric} onPress={onMetricPress} />
      ))}
    </View>
  );
};

// --- NEW COMPONENTS END ---


const GardenCard = ({ garden, index, onPress, onDelete }) => {
  const photoUrl = garden.photos && garden.photos.length > 0
    ? garden.photos[0].photo_url
    : 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&q=80&w=800';

  return (
    <TouchableOpacity
      activeOpacity={0.9}
      onPress={() => onPress(garden)}
      style={[styles.card, { marginLeft: index === 0 ? theme.spacing.margin : 16 }]}
    >
      <Image source={{ uri: photoUrl }} style={styles.cardImage} resizeMode="cover" />
      <View style={styles.cardContent}>
        <View style={styles.cardHeader}>
          <View style={{ flex: 1 }}>
            <Text style={styles.gardenName}>{garden.name}</Text>
            <View style={[styles.statusChip, garden.status === 'Ready' ? styles.statusReady : styles.statusProcessing, { alignSelf: 'flex-start', marginTop: 4 }]}>
              <Text style={styles.statusText}>{garden.status || 'New'}</Text>
            </View>
          </View>
          <TouchableOpacity 
            onPress={(e) => {
              e.stopPropagation();
              onDelete(garden);
            }}
            style={{ padding: 8 }}
          >
            <Trash2 size={20} color={theme.colors.vibrantPink} />
          </TouchableOpacity>
        </View>

        <Text style={[styles.recommendation, { color: theme.colors.primary, fontFamily: 'Manrope_600SemiBold', marginBottom: 4 }]} numberOfLines={1}>
          {garden.summary || "Analyzing..."}
        </Text>

        <Text style={styles.recommendation} numberOfLines={2}>
          {garden.recommendation || "Our AI is analyzing your botanical garden to provide personalized care recommendations..."}
        </Text>

        <View style={styles.cardFooter}>
          <Text style={styles.footerText}>Explore {garden.plants?.length || 0} residents</Text>
          <ChevronRight size={16} color={theme.colors.primary} />
        </View>
      </View>
    </TouchableOpacity>
  );
};

const PlantCard = ({ plant, index, gardenStatus, onPress }) => {
  return (
    <TouchableOpacity onPress={() => onPress(plant)} style={[styles.card, { marginLeft: index === 0 ? theme.spacing.margin : 16, width: CARD_WIDTH - 20 }]}>
      <View style={{position: 'relative'}}>
        {plant.image_url ? (
          <Image source={{ uri: plant.image_url }} style={[styles.cardImage, { height: 220 }]} resizeMode="contain" />
        ) : gardenStatus !== 'Ready' ? (
          <View style={[styles.cardImage, { height: 220, justifyContent: 'center', alignItems: 'center' }]}>
            <ActivityIndicator size="large" color={theme.colors.primary} />
            <Text style={{ marginTop: 12, color: theme.colors.outline, fontFamily: 'Manrope_600SemiBold' }}>Extracting cutout...</Text>
          </View>
        ) : (
          <View style={[styles.cardImage, { height: 220, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.surfaceContainerHigh }]}>
            <ImageIcon size={32} color={theme.colors.outline} />
            <Text style={{ marginTop: 12, color: theme.colors.outline, fontFamily: 'Manrope_600SemiBold' }}>Image unavailable</Text>
          </View>
        )}
      </View>
      <View style={styles.cardContent}>
        <Text style={styles.plantVariety}>{plant.plant_variety || 'Unknown Species'}</Text>
        <Text style={[styles.gardenName, { fontSize: 22, marginBottom: 8 }]}>{plant.name}</Text>

        <View style={styles.conditionBadge}>
          <Text style={styles.conditionText}>{plant.latest_condition || 'Healthy'}</Text>
        </View>

        <Text style={[styles.recommendation, { marginTop: 12, minHeight: 60 }]} numberOfLines={3}>
          {plant.latest_recommendation || "Maintain consistent care to ensure your plant thrives in its current environment."}
        </Text>

        <View style={styles.plantStats}>
          <View style={styles.statItem}>
            <Droplets size={14} color={theme.colors.outline} />
            <Text style={styles.statText}>Normal</Text>
          </View>
          <View style={styles.statItem}>
            <Sun size={14} color={theme.colors.outline} />
            <Text style={styles.statText}>Bright</Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
};

export default function App() {
  const [fontsLoaded, setFontsLoaded] = useState(false);

  useEffect(() => {
    async function loadFonts() {
      try {
        await Font.loadAsync({
          Manrope_400Regular,
          Manrope_600SemiBold,
          Manrope_700Bold,
        });
        setFontsLoaded(true);
      } catch (e) {
        console.warn("Font loading failed, proceeding with system fonts", e);
        setFontsLoaded(true);
      }
    }
    loadFonts();
  }, []);

  const [gardens, setGardens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGarden, setSelectedGarden] = useState(null);
  const [selectedPlant, setSelectedPlant] = useState(null);
  const initialLoadDone = useRef(false);
  const [scrollX, setScrollX] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  const [activeMetric, setActiveMetric] = useState(null);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchData(true);
    } catch (error) {
      console.error(error);
    } finally {
      setRefreshing(false);
    }
  };
  const [uploadData, setUploadData] = useState({ name: '', location: '', photos: [] });
  const [uploadingState, setUploadingState] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);
  const [isLocating, setIsLocating] = useState(false);

  const POPULAR_CITIES = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad', 'New York', 'London', 'Tokyo'];
  
  const filteredCities = uploadData.location.trim() === '' ? [] : POPULAR_CITIES.filter(city => 
    city.toLowerCase().includes(uploadData.location.toLowerCase()) && 
    city.toLowerCase() !== uploadData.location.toLowerCase()
  ).slice(0, 3);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const processingGardens = gardens.filter(g => g.status !== 'Ready');
    if (processingGardens.length === 0) {
      return;
    }

    const interval = setInterval(async () => {
      try {
        await fetchData(true);
      } catch (error) {
        console.error("Failed to poll for garden status", error);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [gardens]);

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('Sorry, we need camera roll permissions to make this work!');
      return;
    }
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.8,
      allowsMultipleSelection: true,
    });
    if (!result.canceled) {
      setUploadData({ ...uploadData, photos: result.assets });
    }
  };

  const handleAddPlants = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('Sorry, we need camera roll permissions to make this work!');
      return;
    }
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      allowsMultipleSelection: true,
      quality: 0.8,
    });
    if (!result.canceled && result.assets && result.assets.length > 0) {
      setUploadingState(true);
      try {
        await uploadGardenPhotos(result.assets, selectedGarden.name, 4, selectedGarden.location);
        fetchData(true);
        alert("Photos uploaded successfully! The AI is analyzing them in the background.");
      } catch (err) {
        console.error("Upload failed", err);
        alert("Failed to upload photos. Please try again.");
      } finally {
        setUploadingState(false);
      }
    }
  };

  const handleUploadSubmit = async () => {
    if (!uploadData.name || uploadData.photos.length === 0) return;
    setUploadingState(true);
    try {
      const newGardenResponse = await uploadGardenPhotos(uploadData.photos, uploadData.name, 4, uploadData.location);
      setUploadData({ name: '', location: '', photos: [] });
      setIsUploading(false);
      
      const data = await getDetailedGardens(4);
      const sorted = data.sort((a, b) => new Date(b.last_accessed_at || b.created_at) - new Date(a.last_accessed_at || a.created_at));
      setGardens(sorted);
      
      const newlyUploadedGarden = sorted.find(g => g.id === newGardenResponse.garden_id);
      if (newlyUploadedGarden) {
        handleGardenPress(newlyUploadedGarden);
      } else {
        await fetchData();
      }
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload garden. Please try again.");
    } finally {
      setUploadingState(false);
    }
  };

  const handleAutoLocate = async () => {
    try {
      setIsLocating(true);
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        alert('Permission to access location was denied');
        return;
      }
      const location = await Location.getCurrentPositionAsync({});
      const geocode = await Location.reverseGeocodeAsync({ latitude: location.coords.latitude, longitude: location.coords.longitude });
      if (geocode.length > 0) {
        const city = geocode[0].city || geocode[0].subregion || geocode[0].region;
        setUploadData(prev => ({ ...prev, location: city }));
      }
    } catch (error) {
      console.error("Error fetching location:", error);
      alert("Failed to find your location. Please enter it manually.");
    } finally {
      setIsLocating(false);
    }
  };

  const handleGardenPress = (garden) => {
    setSelectedGarden(garden);
  };

  const performDelete = async (garden) => {
    try {
      await deleteGarden(garden.id);
      const data = await getDetailedGardens(4);
      setGardens(data);
      if (selectedGarden && selectedGarden.id === garden.id) {
        setSelectedGarden(null);
      }
    } catch (error) {
      console.error("Delete failed", error);
      if (Platform.OS === 'web') {
        window.alert("Failed to delete garden. Please try again.");
      } else {
        Alert.alert("Error", "Failed to delete garden. Please try again.");
      }
    }
  };

  const handleDeleteGarden = (garden) => {
    if (Platform.OS === 'web') {
      const confirmDelete = window.confirm(`Are you sure you want to delete "${garden.name}"? This action cannot be undone.`);
      if (confirmDelete) {
        performDelete(garden);
      }
    } else {
      Alert.alert(
        "Delete Garden",
        `Are you sure you want to delete "${garden.name}"? This action cannot be undone.`,
        [
          { text: "Cancel", style: "cancel" },
          { 
            text: "Delete", 
            style: "destructive",
            onPress: () => performDelete(garden)
          }
        ]
      );
    }
  };

  const fetchData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const data = await getDetailedGardens(4);
      const sorted = [...data].sort((a, b) => new Date(b.last_accessed_at || 0) - new Date(a.last_accessed_at || 0));
      setGardens(sorted);
      
      if (selectedGarden) {
        const updatedSelected = sorted.find(g => g.id === selectedGarden.id);
        if (updatedSelected) {
          setSelectedGarden(updatedSelected);
        }
      } else if (!initialLoadDone.current) {
        if (sorted.length > 0) {
          handleGardenPress(sorted[0]);
        } else {
          setIsUploading(true);
        }
        initialLoadDone.current = true;
      }
    } catch (error) {
      console.error(error);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  if (!fontsLoaded || loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>Gathering botanical insights...</Text>
      </View>
    );
  }

  const getAnalysisMessage = () => {
    return selectedGarden?.upload_commentry || 'Photo Analysis in progress...';
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      
      {selectedPlant ? (
        <PlantDetails plant={selectedPlant} onBack={() => setSelectedPlant(null)} onUpdate={() => fetchData(true)} />
      ) : isUploading ? (
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
          <TouchableOpacity style={styles.backButton} onPress={() => setIsUploading(false)}>
            <ArrowLeft size={20} color={theme.colors.primary} />
            <Text style={styles.backText}>Cancel</Text>
          </TouchableOpacity>
          <View style={[styles.header, { marginTop: 10, marginBottom: 20 }]}>
            <View style={styles.logoContainer}>
              <Leaf size={18} color={theme.colors.primary} />
              <Text style={styles.logoText}>ADD NEW GROWTH</Text>
            </View>
            <Text style={[styles.title, { fontSize: 28 }]}>Capture Garden</Text>
          </View>
          <ScrollView contentContainerStyle={{ paddingHorizontal: theme.spacing.margin }}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Garden Name</Text>
              <TextInput style={styles.textInput} placeholder="e.g. Sunny Balcony" value={uploadData.name} onChangeText={(text) => setUploadData({ ...uploadData, name: text })} />
            </View>
            <View style={[styles.inputGroup, { zIndex: 10 }]}>
              <Text style={styles.inputLabel}>Location (City)</Text>
              <View style={styles.locationInputContainer}>
                <TextInput style={[styles.textInput, { flex: 1, borderBottomWidth: 0 }]} placeholder="e.g. Bangalore" value={uploadData.location} onFocus={() => setShowLocationSuggestions(true)} onBlur={() => setTimeout(() => setShowLocationSuggestions(false), 200)} onChangeText={(text) => { setUploadData({ ...uploadData, location: text }); setShowLocationSuggestions(true); }} />
                <TouchableOpacity onPress={handleAutoLocate} disabled={isLocating} style={{ padding: 8 }}>
                  {isLocating ? <ActivityIndicator size="small" color={theme.colors.primary} /> : <MapPin size={20} color={theme.colors.primary} />}
                </TouchableOpacity>
              </View>
              {showLocationSuggestions && filteredCities.length > 0 && (
                <View style={styles.suggestionsContainer}>
                  {filteredCities.map((city) => (
                    <TouchableOpacity key={city} style={styles.suggestionItem} onPress={() => { setUploadData({ ...uploadData, location: city }); setShowLocationSuggestions(false); }}>
                      <Text style={styles.suggestionText}>{city}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Plant Photos</Text>
              <TouchableOpacity style={styles.uploadZone} onPress={pickImage}>
                {uploadData.photos.length > 0 ? (
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ width: '100%', marginBottom: 16 }} contentContainerStyle={{ gap: 8 }}>
                    {uploadData.photos.map((photo, index) => <Image key={index} source={{ uri: photo.uri }} style={{ width: 80, height: 80, borderRadius: 8 }} />)}
                  </ScrollView>
                ) : <ImageIcon size={40} color={theme.colors.outline} style={{ marginBottom: 16 }} />}
                <Text style={styles.uploadText}>{uploadData.photos.length > 0 ? `${uploadData.photos.length} photos selected` : "Tap to select photos"}</Text>
                <Text style={styles.uploadSubtext}>High-res JPG or PNG works best</Text>
              </TouchableOpacity>
            </View>
            <TouchableOpacity style={[styles.btnPrimary, (uploadingState || uploadData.photos.length === 0 || !uploadData.name) ? { backgroundColor: theme.colors.surfaceContainerHigh } : { backgroundColor: theme.colors.vibrantPink }]} onPress={handleUploadSubmit} disabled={uploadingState || uploadData.photos.length === 0 || !uploadData.name}>
              {uploadingState ? <ActivityIndicator color={theme.colors.onSurfaceVariant} size="small" /> : <Sparkles size={20} color={(uploadData.photos.length === 0 || !uploadData.name) ? theme.colors.onSurfaceVariant : '#ffffff'} />}
              <Text style={[styles.btnPrimaryText, (uploadingState || uploadData.photos.length === 0 || !uploadData.name) ? { color: theme.colors.onSurfaceVariant } : { color: '#ffffff' }]}>{uploadingState ? 'Analyzing...' : 'Upload and Analyze'}</Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      ) : !selectedGarden ? (
        <ScrollView style={{ flex: 1 }} contentContainerStyle={{ flexGrow: 1 }} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}>
          <View style={[styles.header, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}>
            <View>
              <View style={styles.logoContainer}><Leaf size={18} color={theme.colors.primary} /><Text style={styles.logoText}>BOTANICAL MANAGER</Text></View>
              <Text style={styles.title}>My Gardens</Text>
            </View>
            <TouchableOpacity style={styles.btnIcon} onPress={() => setIsUploading(true)}><Plus size={24} color={theme.colors.tertiary} /></TouchableOpacity>
          </View>
          {gardens.length > 0 ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingRight: theme.spacing.margin }} snapToInterval={CARD_WIDTH + 16} decelerationRate="fast" onScroll={(e) => setScrollX(e.nativeEvent.contentOffset.x)} scrollEventThrottle={16}>
              {gardens.map((garden, index) => <GardenCard key={garden.id} garden={garden} index={index} onPress={handleGardenPress} onDelete={handleDeleteGarden} />)}
            </ScrollView>
          ) : (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40, marginTop: 40 }}>
              <View style={{ width: 120, height: 120, borderRadius: 60, backgroundColor: theme.colors.surfaceContainerLowest, justifyContent: 'center', alignItems: 'center', marginBottom: 24 }}><Leaf size={60} color={theme.colors.primary} opacity={0.5} /></View>
              <Text style={[styles.title, { textAlign: 'center', marginBottom: 12 }]}>Bring Your Garden to Life</Text>
              <Text style={[styles.recommendation, { textAlign: 'center', fontSize: 16, lineHeight: 24 }]}>Upload photos of your garden to get personalized AI care recommendations.</Text>
              <TouchableOpacity style={[styles.btnPrimary, { marginTop: 32, width: '100%', backgroundColor: theme.colors.vibrantPink }]} onPress={() => setIsUploading(true)}><Plus size={20} color="#ffffff" /><Text style={[styles.btnPrimaryText, { color: '#ffffff' }]}>Initialize First Analysis</Text></TouchableOpacity>
            </View>
          )}
          <View style={styles.progressBarContainer}><View style={styles.progressBar}><View style={[styles.progressIndicator, { width: gardens.length > 0 ? (scrollX / (gardens.length * (CARD_WIDTH + 16))) * 100 + '%' : '0%' }]} /></View></View>
        </ScrollView>
      ) : (
        <ScrollView style={{ flex: 1 }} contentContainerStyle={{ flexGrow: 1 }} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingRight: theme.spacing.margin }}>
            <TouchableOpacity style={styles.backButton} onPress={() => setSelectedGarden(null)}><ArrowLeft size={20} color={theme.colors.primary} /><Text style={styles.backText}>Back to Gardens</Text></TouchableOpacity>
            <TouchableOpacity style={[styles.backButton, { backgroundColor: 'transparent' }]} onPress={() => handleDeleteGarden(selectedGarden)}><Trash2 size={20} color={theme.colors.vibrantPink} /><Text style={[styles.backText, { color: theme.colors.vibrantPink }]}>Delete</Text></TouchableOpacity>
          </View>
          <View style={styles.heroContainer}>
            {selectedGarden.photos && selectedGarden.photos.length > 0 ? <Image source={{ uri: selectedGarden.photos[0].photo_url }} style={styles.heroImage} resizeMode="cover" /> : <View style={[styles.heroImage, { backgroundColor: theme.colors.surfaceContainerHigh }]} />}
            <View style={styles.heroOverlay}><Text style={styles.heroTitle}>{selectedGarden.name}</Text>{!!selectedGarden.location && <Text style={styles.heroLocation}>{selectedGarden.location}</Text>}</View>
          </View>
          {selectedGarden.status !== 'Ready' && (
            <View style={styles.analysisContainer}>
              <ActivityIndicator size="small" color={theme.colors.vibrantPink} />
              <View style={{ flexShrink: 1 }}>
                <Text style={styles.analysisText}>{getAnalysisMessage()}</Text>
              </View>
            </View>
          )}

          {/* --- MODIFIED SECTION --- */}
          {selectedGarden.status === 'Ready' && selectedGarden.healthOverview && (
            <View style={{ paddingHorizontal: theme.spacing.margin, marginTop: 24 }}>
              <SanctuaryVitalityCard vitality={selectedGarden.healthOverview.sanctuaryVitality} />
              <MetricTileGrid metrics={selectedGarden.healthOverview.metrics} onMetricPress={setActiveMetric} />
            </View>
          )}
          {/* --- END MODIFIED SECTION --- */}

          <View style={[styles.header, { marginTop: 20, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}>
            <Text style={[styles.title, { fontSize: 28, marginBottom: 0 }]}>Botanical Residents</Text>
            {uploadingState ? <ActivityIndicator size="small" color={theme.colors.primary} /> : <TouchableOpacity onPress={handleAddPlants} style={{ padding: 8, backgroundColor: theme.colors.surfaceContainerHigh, borderRadius: 20 }}><Plus size={20} color={theme.colors.primary} /></TouchableOpacity>}
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingRight: theme.spacing.margin }} snapToInterval={CARD_WIDTH - 4} decelerationRate="fast">
            {selectedGarden.plants.length > 0 ? (
              selectedGarden.plants.map((plant, index) => <PlantCard key={plant.id} plant={plant} index={index} gardenStatus={selectedGarden.status} onPress={setSelectedPlant} />)
            ) : (
              <View style={[styles.loadingContainer, { width: width - 48, height: 300 }]}><Leaf size={40} color={theme.colors.outline} opacity={0.3} /><Text style={styles.loadingText}>No residents yet</Text></View>
            )}
          </ScrollView>
        </ScrollView>
      )}

      {/* Triage Bottom Sheet Modal */}
      <Modal
        visible={activeMetric !== null}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setActiveMetric(null)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <View>
                <Text style={styles.modalSubTitle}>{activeMetric?.category?.replace('_', ' ')} DETAILS</Text>
                <Text style={styles.modalTitle}>
                  Status:{' '}
                  <Text style={activeMetric?.isUnfavorable ? { color: theme.colors.vibrantPink } : { color: 'green' }}>
                    {activeMetric?.isUnfavorable ? activeMetric.status : 'Optimal'}
                  </Text>
                </Text>
              </View>
              <TouchableOpacity onPress={() => setActiveMetric(null)} style={styles.modalCloseButton}>
                <Text style={{ fontSize: 16, fontWeight: 'bold', color: theme.colors.outline }}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView style={{ flex: 1, marginTop: 16 }}>
              {activeMetric?.isUnfavorable ? (
                selectedGarden?.plants.filter(p => activeMetric.affectedPlantIds.includes(p.id)).length > 0 ? (
                  selectedGarden?.plants.filter(p => activeMetric.affectedPlantIds.includes(p.id)).map((plant) => (
                    <View key={plant.id} style={styles.modalPlantCard}>
                      {plant.image_url ? (
                        <Image source={{ uri: plant.image_url }} style={styles.modalPlantImage} />
                      ) : (
                        <View style={[styles.modalPlantImage, { backgroundColor: theme.colors.surfaceContainerHigh, justifyContent: 'center', alignItems: 'center' }]}>
                          <Leaf size={24} color={theme.colors.outline} />
                        </View>
                      )}
                      <View style={{ flex: 1, justifyContent: 'space-between' }}>
                        <View>
                          <Text style={styles.modalPlantName}>{plant.name}</Text>
                          <Text style={styles.modalPlantVariety}>{plant.plant_variety || 'Unknown Species'}</Text>
                        </View>
                        
                        <View style={styles.issueHighlight}>
                          <Text style={styles.issueHighlightText}>
                            {activeMetric.category === 'WATERING' && `Needs watering: ${plant.latest_condition || 'Dry/Overwatered'}`}
                            {activeMetric.category === 'SUN_EXPOSURE' && `Inadequate lighting: ${plant.latest_condition || 'Poor exposure'}`}
                            {activeMetric.category === 'SOIL_QUALITY' && `Needs fertilizer: ${plant.latest_condition || 'Nutrient deficit'}`}
                            {activeMetric.category === 'VITALITY' && `Stagnant growth: ${plant.latest_condition || 'Low momentum'}`}
                            {activeMetric.category === 'LEAF_CARE' && `Leaf Care Overdue: ${plant.latest_condition || 'Dusty leaves'}`}
                            {activeMetric.category === 'POT_STATUS' && `Cramped Pot: ${plant.latest_condition || 'Needs repotting'}`}
                            {activeMetric.category === 'PRUNING' && `Overdue Trimming: ${plant.latest_condition || 'Overgrown/Dead leaves'}`}
                          </Text>
                        </View>
                      </View>
                    </View>
                  ))
                ) : (
                  <Text style={styles.emptyText}>No specific plants registered with this issue.</Text>
                )
              ) : (
                <View style={{ alignItems: 'center', paddingVertical: 32 }}>
                  <View style={{ width: 64, height: 64, borderRadius: 32, backgroundColor: '#e8f5e9', justifyContent: 'center', alignItems: 'center', marginBottom: 16 }}>
                    <CheckCircle2 size={36} color="green" />
                  </View>
                  <Text style={[styles.modalPlantName, { marginBottom: 4 }]}>All Good!</Text>
                  <Text style={[styles.emptyText, { marginTop: 0 }]}>All plants in this sanctuary are healthy and have optimal conditions.</Text>
                </View>
              )}
            </ScrollView>

            <TouchableOpacity style={styles.modalDismissButton} onPress={() => setActiveMetric(null)}>
              <Text style={styles.modalDismissButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.background },
  loadingText: { marginTop: 16, color: theme.colors.primary, fontFamily: 'Manrope_600SemiBold' },
  header: { padding: theme.spacing.margin, marginTop: 20 },
  logoContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  logoText: { fontFamily: 'Manrope_700Bold', fontSize: 12, letterSpacing: 1.2, color: theme.colors.primary, marginLeft: 6 },
  title: { fontFamily: 'Manrope_700Bold', fontSize: 34, color: theme.colors.primary },
  card: { width: CARD_WIDTH, backgroundColor: 'white', borderRadius: theme.roundness.xl, overflow: 'hidden', shadowColor: theme.colors.primary, shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.05, shadowRadius: 20, elevation: 5, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(85, 97, 88, 0.05)' },
  cardImage: { width: '100%', height: 300, backgroundColor: theme.colors.surfaceContainerLowest },
  cardContent: { padding: 20 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 },
  gardenName: { fontFamily: 'Manrope_600SemiBold', fontSize: 18, color: theme.colors.primary, flex: 1, marginRight: 10 },
  statusChip: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  statusReady: { backgroundColor: theme.colors.primaryContainer },
  statusProcessing: { backgroundColor: '#fff3e0' },
  statusText: { fontSize: 10, fontFamily: 'Manrope_700Bold', color: theme.colors.tertiary, textTransform: 'uppercase' },
  recommendation: { fontFamily: 'Manrope_400Regular', fontSize: 14, color: '#666', lineHeight: 20 },
  cardFooter: { flexDirection: 'row', alignItems: 'center', marginTop: 20, paddingTop: 16, borderTopWidth: 1, borderTopColor: theme.colors.surfaceContainer },
  footerText: { fontFamily: 'Manrope_600SemiBold', fontSize: 13, color: theme.colors.primary, flex: 1 },
  plantVariety: { fontFamily: 'Manrope_700Bold', fontSize: 11, color: theme.colors.tertiary, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  conditionBadge: { backgroundColor: '#f1f8e9', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4, alignSelf: 'flex-start' },
  conditionText: { color: '#2e7d32', fontFamily: 'Manrope_700Bold', fontSize: 11 },
  plantStats: { flexDirection: 'row', gap: 15, marginTop: 20, paddingTop: 15, borderTopWidth: 1, borderTopColor: theme.colors.surfaceContainer },
  statItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  statText: { fontFamily: 'Manrope_400Regular', fontSize: 12, color: theme.colors.outline },
  progressBarContainer: { paddingHorizontal: theme.spacing.margin, marginTop: 10, marginBottom: 40 },
  progressBar: { height: 3, backgroundColor: theme.colors.surfaceContainer, borderRadius: 2, position: 'relative', overflow: 'hidden' },
  progressIndicator: { position: 'absolute', top: 0, left: 0, height: '100%', backgroundColor: theme.colors.primary },
  backButton: { flexDirection: 'row', alignItems: 'center', padding: theme.spacing.margin, paddingBottom: 0 },
  backText: { fontFamily: 'Manrope_600SemiBold', fontSize: 14, color: theme.colors.primary, marginLeft: 8 },
  inputGroup: { marginBottom: 24 },
  inputLabel: { fontFamily: 'Manrope_600SemiBold', fontSize: 14, color: theme.colors.primary, marginBottom: 8 },
  textInput: { backgroundColor: 'white', borderWidth: 1, borderColor: theme.colors.outline, borderRadius: theme.roundness.md, padding: theme.spacing.md, fontFamily: 'Manrope_400Regular', fontSize: 16, color: theme.colors.onSurface },
  locationInputContainer: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: theme.colors.surfaceContainer },
  suggestionsContainer: { backgroundColor: 'white', borderWidth: 1, borderColor: theme.colors.outlineVariant + '4D', borderBottomLeftRadius: theme.roundness.md, borderBottomRightRadius: theme.roundness.md, borderTopWidth: 0, marginTop: -4, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 10, elevation: 3, position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 20, maxHeight: 150 },
  suggestionItem: { padding: theme.spacing.sm, paddingHorizontal: theme.spacing.md, borderBottomWidth: 1, borderBottomColor: theme.colors.surfaceContainer },
  suggestionText: { fontFamily: 'Manrope_400Regular', fontSize: 14, color: theme.colors.onSurface },
  uploadZone: { borderWidth: 2, borderStyle: 'dashed', borderColor: theme.colors.surfaceContainerHigh, borderRadius: theme.roundness.lg, padding: 40, alignItems: 'center', backgroundColor: theme.colors.background },
  uploadText: { fontFamily: 'Manrope_600SemiBold', fontSize: 16, color: theme.colors.primary, marginBottom: 4 },
  uploadSubtext: { fontFamily: 'Manrope_400Regular', fontSize: 12, color: theme.colors.outline },
  btnPrimary: { backgroundColor: theme.colors.secondaryContainer, borderRadius: 48, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 32, gap: 8 },
  btnPrimaryText: { fontFamily: 'Manrope_700Bold', fontSize: 16, color: theme.colors.onSecondaryContainer },
  btnIcon: { backgroundColor: theme.colors.primaryContainer, width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center' },
  heroContainer: { marginHorizontal: theme.spacing.margin, marginTop: theme.spacing.sm, height: 320, borderRadius: 32, overflow: 'hidden', position: 'relative', borderWidth: 1, borderColor: theme.colors.outlineVariant + '4D' },
  heroImage: { width: '100%', height: '100%', resizeMode: 'cover' },
  heroOverlay: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: theme.spacing.md, backgroundColor: 'rgba(0,0,0,0.4)' },
  heroTitle: { fontFamily: 'Manrope_700Bold', fontSize: 32, color: '#ffffff' },
  heroLocation: { fontFamily: 'Manrope_600SemiBold', fontSize: 14, color: '#ffffff', opacity: 0.9, marginTop: 4 },
  analysisContainer: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.primaryContainer, marginHorizontal: theme.spacing.margin, marginTop: theme.spacing.md, marginBottom: theme.spacing.md, padding: theme.spacing.md, borderRadius: theme.roundness.lg, gap: 12 },
  analysisText: { fontFamily: 'Manrope_600SemiBold', fontSize: 14, color: theme.colors.onSurfaceVariant, flexShrink: 1 },
  
  // --- NEW STYLES ---
  vitalityCard: {
    backgroundColor: '#1A3C34', // Custom dark green, or theme.colors.primary
    borderRadius: theme.roundness.xl,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  vitalityContent: {
    flex: 1,
  },
  vitalityLabel: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 10,
    color: theme.colors.primaryContainer,
    letterSpacing: 1,
    opacity: 0.8,
    marginBottom: 4,
  },
  vitalityScore: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 40,
    color: 'white',
  },
  vitalitySummary: {
    fontFamily: 'Manrope_400Regular',
    fontSize: 12,
    color: theme.colors.outlineVariant,
    marginTop: 4,
  },
  vitalityChart: {
    width: 80,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
  },
  vitalityChartIcon: {
    position: 'absolute',
  },
  metricGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  metricTile: {
    width: (width - (theme.spacing.margin * 2) - 24) / 3, // 3 columns with 12px gap
    height: 120,
    backgroundColor: theme.colors.surfaceContainerLowest,
    borderRadius: theme.roundness.lg,
    borderWidth: 1,
    borderColor: theme.colors.surfaceContainerHigh,
    padding: 12,
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  metricBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: theme.colors.vibrantPink,
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1,
  },
  metricBadgeText: {
    color: 'white',
    fontFamily: 'Manrope_700Bold',
    fontSize: 10,
  },
  metricLabel: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 10,
    color: theme.colors.outline,
    textAlign: 'center',
    textTransform: 'uppercase',
    marginTop: 4,
  },
  metricStatus: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 16,
    color: theme.colors.primary,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(1, 38, 31, 0.4)',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: 'white',
    width: '100%',
    maxHeight: '85%',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -10 },
    shadowOpacity: 0.1,
    shadowRadius: 20,
    elevation: 10,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#eaf6f2',
    paddingBottom: 16,
  },
  modalSubTitle: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 10,
    color: '#717976',
    letterSpacing: 1,
  },
  modalTitle: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 22,
    color: '#1a3c34',
    marginTop: 4,
  },
  modalCloseButton: {
    backgroundColor: '#f1f4f3',
    padding: 8,
    borderRadius: 20,
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalPlantCard: {
    flexDirection: 'row',
    gap: 16,
    padding: 16,
    backgroundColor: '#f7faf9',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#eaf6f2',
    marginBottom: 12,
  },
  modalPlantImage: {
    width: 64,
    height: 64,
    borderRadius: 12,
    backgroundColor: '#dfebe6',
  },
  modalPlantName: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 16,
    color: '#1a3c34',
  },
  modalPlantVariety: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 12,
    color: '#717976',
    textTransform: 'capitalize',
  },
  issueHighlight: {
    marginTop: 8,
    backgroundColor: 'rgba(209, 0, 86, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(209, 0, 86, 0.2)',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  issueHighlightText: {
    color: '#D10056',
    fontFamily: 'Manrope_700Bold',
    fontSize: 11,
  },
  emptyText: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 14,
    color: '#717976',
    textAlign: 'center',
    marginTop: 24,
  },
  modalDismissButton: {
    backgroundColor: '#1a3c34',
    paddingVertical: 16,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 16,
  },
  modalDismissButtonText: {
    color: 'white',
    fontFamily: 'Manrope_700Bold',
    fontSize: 16,
  },
});
