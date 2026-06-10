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
  Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { theme } from './src/theme';
import { getDetailedGardens, uploadGardenPhotos, updateGardenAccess, getGardenEnvironment, deleteGarden, uploadPlantPhoto } from './src/services/api';
import { Leaf, ChevronRight, ArrowLeft, Droplets, Sun, Plus, Image as ImageIcon, Sparkles, Thermometer, MapPin, Trash2 } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import * as Font from 'expo-font';
import { Manrope_400Regular, Manrope_600SemiBold, Manrope_700Bold } from '@expo-google-fonts/manrope';
import PlantDetails from './src/components/PlantDetails';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width * 0.85;
const SPACER = (width - CARD_WIDTH) / 2;

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
        setFontsLoaded(true); // Proceed anyway to avoid stuck screen
      }
    }
    loadFonts();
  }, []);

  const [gardens, setGardens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGarden, setSelectedGarden] = useState(null);
  const [selectedPlant, setSelectedPlant] = useState(null);
  const [environmentData, setEnvironmentData] = useState(null);
  const initialLoadDone = useRef(false);
  const [scrollX, setScrollX] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      const data = await getDetailedGardens(4);
      setGardens(data);
      if (selectedGarden) {
        const updatedSelected = data.find(g => g.id === selectedGarden.id);
        if (updatedSelected) {
          setSelectedGarden(updatedSelected);
        } else {
          setSelectedGarden(null);
        }
      }
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

  const pickImage = async () => {
    // Request permissions explicitly
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('Sorry, we need camera roll permissions to make this work!');
      return;
    }

    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.8,
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
      
      // Fetch the fully populated list of gardens (including photos)
      const data = await getDetailedGardens(4);
      const sorted = data.sort((a, b) => {
        const dateA = a.last_accessed_at ? new Date(a.last_accessed_at) : new Date(a.created_at);
        const dateB = b.last_accessed_at ? new Date(b.last_accessed_at) : new Date(b.created_at);
        return dateB - dateA;
      });
      setGardens(sorted);

      // Find the newly uploaded garden with its full details (photos, etc.) and auto-select it
      const newlyUploadedGarden = sorted.find(g => g.id === newGardenResponse.id);
      if (newlyUploadedGarden) {
        handleGardenPress(newlyUploadedGarden);
      } else {
        await fetchData(); // fallback
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
      const geocode = await Location.reverseGeocodeAsync({
        latitude: location.coords.latitude,
        longitude: location.coords.longitude
      });

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

  const handleGardenPress = async (garden) => {
    setSelectedGarden(garden);
    setEnvironmentData(null);
    updateGardenAccess(garden.id).catch(console.error);
    try {
      const env = await getGardenEnvironment(garden.id);
      setEnvironmentData(env);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteGarden = (garden) => {
    Alert.alert(
      "Delete Garden",
      `Are you sure you want to delete "${garden.name}"? This action cannot be undone.`,
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Delete", 
          style: "destructive",
          onPress: async () => {
            try {
              await deleteGarden(garden.id);
              const data = await getDetailedGardens(4);
              setGardens(data);
              if (selectedGarden && selectedGarden.id === garden.id) {
                setSelectedGarden(null);
              }
            } catch (error) {
              console.error("Delete failed", error);
              Alert.alert("Error", "Failed to delete garden. Please try again.");
            }
          }
        }
      ]
    );
  };

  const fetchData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const data = await getDetailedGardens(4);
      const sorted = [...data].sort((a, b) => new Date(b.last_accessed_at || 0) - new Date(a.last_accessed_at || 0));
      setGardens(sorted);
      
      // Update selectedGarden if it exists to refresh its status and commentary
      if (selectedGarden) {
        const updatedSelected = sorted.find(g => g.id === selectedGarden.id);
        if (updatedSelected) {
          setSelectedGarden(updatedSelected);
          // If it was processing and is still processing, or just became ready, refresh environment data
          if (selectedGarden.status !== 'Ready') {
            getGardenEnvironment(updatedSelected.id)
              .then(env => setEnvironmentData(env))
              .catch(console.error);
          }
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

    useEffect(() => {
      let interval;
      const hasProcessing = gardens.some(g => g.status !== 'Ready');
      if (hasProcessing) {
        interval = setInterval(() => {
          fetchData(true);
        }, 5000);
      }
      return () => clearInterval(interval);
    }, [gardens, selectedGarden]);

  if (!fontsLoaded || loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>Gathering botanical insights...</Text>
      </View>
    );
  }

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
              <TextInput
                style={styles.textInput}
                placeholder="e.g. Sunny Balcony, Indoor Jungle"
                value={uploadData.name}
                onChangeText={(text) => setUploadData({ ...uploadData, name: text })}
              />
            </View>

            <View style={[styles.inputGroup, { zIndex: 10 }]}>
              <Text style={styles.inputLabel}>Location (City)</Text>
              <View style={styles.locationInputContainer}>
                <TextInput
                  style={[styles.textInput, { flex: 1, borderBottomWidth: 0 }]}
                  placeholder="e.g. Bangalore, Mumbai"
                  value={uploadData.location}
                  onFocus={() => setShowLocationSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowLocationSuggestions(false), 200)}
                  onChangeText={(text) => {
                    setUploadData({ ...uploadData, location: text });
                    setShowLocationSuggestions(true);
                  }}
                />
                <TouchableOpacity onPress={handleAutoLocate} disabled={isLocating} style={{ padding: 8 }}>
                  {isLocating ? (
                    <ActivityIndicator size="small" color={theme.colors.primary} />
                  ) : (
                    <MapPin size={20} color={theme.colors.primary} />
                  )}
                </TouchableOpacity>
              </View>
              {showLocationSuggestions && filteredCities.length > 0 && (
                <View style={styles.suggestionsContainer}>
                  {filteredCities.map((city) => (
                    <TouchableOpacity 
                      key={city} 
                      style={styles.suggestionItem}
                      onPress={() => {
                        setUploadData({ ...uploadData, location: city });
                        setShowLocationSuggestions(false);
                      }}
                    >
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
                  <ScrollView 
                    horizontal 
                    showsHorizontalScrollIndicator={false} 
                    style={{ width: '100%', marginBottom: 16 }}
                    contentContainerStyle={{ gap: 8 }}
                  >
                    {uploadData.photos.map((photo, index) => (
                      <Image 
                        key={index} 
                        source={{ uri: photo.uri }} 
                        style={{ width: 80, height: 80, borderRadius: 8 }} 
                      />
                    ))}
                  </ScrollView>
                ) : (
                  <ImageIcon size={40} color={theme.colors.outline} style={{ marginBottom: 16 }} />
                )}
                <Text style={styles.uploadText}>
                  {uploadData.photos.length > 0 
                    ? `${uploadData.photos.length} photos selected` 
                    : "Tap to select photos"}
                </Text>
                <Text style={styles.uploadSubtext}>High-res JPG or PNG works best</Text>
                <Text style={[styles.uploadSubtext, { marginTop: 4, textAlign: 'center', paddingHorizontal: 20 }]}>
                  You can upload multiple photos to cover all the plants in your garden.
                </Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity 
              style={[
                styles.btnPrimary, 
                (uploadingState || uploadData.photos.length === 0 || !uploadData.name) 
                  ? { backgroundColor: theme.colors.surfaceContainerHigh }
                  : { backgroundColor: theme.colors.vibrantPink }
              ]}
              onPress={handleUploadSubmit}
              disabled={uploadingState || uploadData.photos.length === 0 || !uploadData.name}
            >
              {uploadingState ? (
                <ActivityIndicator color={theme.colors.onSurfaceVariant} size="small" />
              ) : (
                <Sparkles 
                  size={20} 
                  color={(uploadData.photos.length === 0 || !uploadData.name) ? theme.colors.onSurfaceVariant : '#ffffff'} 
                />
              )}
              <Text style={[
                styles.btnPrimaryText,
                (uploadingState || uploadData.photos.length === 0 || !uploadData.name) 
                  ? { color: theme.colors.onSurfaceVariant }
                  : { color: '#ffffff' }
              ]}>
                {uploadingState ? 'Analyzing...' : 'Initialize AI Analysis'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      ) : !selectedGarden ? (

        <ScrollView 
          style={{ flex: 1 }} 
          contentContainerStyle={{ flexGrow: 1 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
        >
          <View style={[styles.header, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}>
            <View>
              <View style={styles.logoContainer}>
                <Leaf size={18} color={theme.colors.primary} />
                <Text style={styles.logoText}>BOTANICAL MANAGER</Text>
              </View>
              <Text style={styles.title}>My Gardens</Text>
            </View>
            <TouchableOpacity style={styles.btnIcon} onPress={() => setIsUploading(true)}>
              <Plus size={24} color={theme.colors.tertiary} />
            </TouchableOpacity>
          </View>

          {gardens.length > 0 ? (
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={{ paddingRight: theme.spacing.margin }}
              snapToInterval={CARD_WIDTH + 16}
              decelerationRate="fast"
              onScroll={(e) => {
                const x = e.nativeEvent.contentOffset.x;
                setScrollX(x);
              }}
              scrollEventThrottle={16}
            >
              {gardens.map((garden, index) => (
                <GardenCard
                  key={garden.id}
                  garden={garden}
                  index={index}
                  onPress={setSelectedGarden}
                  onDelete={handleDeleteGarden}
                />
              ))}
            </ScrollView>
          ) : (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 40, marginTop: 40 }}>
              <View style={{ width: 120, height: 120, borderRadius: 60, backgroundColor: theme.colors.surfaceContainerLowest, justifyContent: 'center', alignItems: 'center', marginBottom: 24 }}>
                <Leaf size={60} color={theme.colors.primary} opacity={0.5} />
              </View>
              <Text style={[styles.title, { textAlign: 'center', marginBottom: 12 }]}>Bring Your Garden to Life</Text>
              <Text style={[styles.recommendation, { textAlign: 'center', fontSize: 16, lineHeight: 24 }]}>
                It looks like you haven't started your botanical journey yet. Upload photos of your garden to get personalized AI care recommendations.
              </Text>
              
              <TouchableOpacity 
                style={[styles.btnPrimary, { marginTop: 32, width: '100%', backgroundColor: theme.colors.vibrantPink }]} 
                onPress={() => setIsUploading(true)}
              >
                <Plus size={20} color="#ffffff" />
                <Text style={[styles.btnPrimaryText, { color: '#ffffff' }]}>Initialize First Analysis</Text>
              </TouchableOpacity>
            </View>
          )}

          <View style={styles.progressBarContainer}>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressIndicator,
                  { width: gardens.length > 0 ? (scrollX / (gardens.length * ( CARD_WIDTH + 16))) * 100 + '%' : '0%' }
                ]}
              />
            </View>
          </View>
        </ScrollView>
      ) : (
        <ScrollView 
          style={{ flex: 1 }} 
          contentContainerStyle={{ flexGrow: 1 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.primary} />}
        >
          {gardens.length === 1 ? (
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingRight: theme.spacing.margin }}>
              <TouchableOpacity style={styles.backButton} onPress={() => setIsUploading(true)}>
                <Plus size={20} color={theme.colors.primary} />
                <Text style={styles.backText}>Add Garden</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.backButton, { backgroundColor: 'transparent' }]} onPress={() => handleDeleteGarden(selectedGarden)}>
                <Trash2 size={20} color={theme.colors.vibrantPink} />
                <Text style={[styles.backText, { color: theme.colors.vibrantPink }]}>Delete</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingRight: theme.spacing.margin }}>
              <TouchableOpacity style={styles.backButton} onPress={() => setSelectedGarden(null)}>
                <ArrowLeft size={20} color={theme.colors.primary} />
                <Text style={styles.backText}>Back to Gardens</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.backButton, { backgroundColor: 'transparent' }]} onPress={() => handleDeleteGarden(selectedGarden)}>
                <Trash2 size={20} color={theme.colors.vibrantPink} />
                <Text style={[styles.backText, { color: theme.colors.vibrantPink }]}>Delete</Text>
              </TouchableOpacity>
            </View>
          )}

          <View style={styles.heroContainer}>
            {selectedGarden.photos && selectedGarden.photos.length > 0 ? (
              <Image source={{ uri: selectedGarden.photos[0].photo_url }} style={styles.heroImage} resizeMode="cover" />
            ) : (
              <View style={[styles.heroImage, { backgroundColor: theme.colors.surfaceContainerHigh }]} />
            )}
            <View style={styles.heroOverlay}>
              <Text style={styles.heroTitle}>{selectedGarden.name}</Text>
              {!!selectedGarden.location && <Text style={styles.heroLocation}>{selectedGarden.location}</Text>}
            </View>
          </View>

          {selectedGarden.status !== 'Ready' && (
            <View style={styles.analysisContainer}>
              <ActivityIndicator size="small" color={theme.colors.vibrantPink} />
              <View style={{ flexShrink: 1 }}>
                <Text style={styles.analysisText}>Photo Analysis in progress...</Text>
                {!!selectedGarden.upload_commentry && (
                  <Text style={[styles.analysisText, { marginTop: 4, fontFamily: 'Manrope_400Regular', color: theme.colors.outline }]}>
                    {selectedGarden.upload_commentry}
                  </Text>
                )}
              </View>
            </View>
          )}

          <View style={styles.tilesGrid}>
            <View style={styles.envTile}>
              <View style={styles.envTileHeader}>
                <Droplets size={24} color={theme.colors.tertiary} />
                <Text style={styles.envTileLabel}>Hydration</Text>
              </View>
              <Text style={styles.envTileValue}>{environmentData?.hydration || '--'}</Text>
            </View>
            <View style={styles.envTile}>
              <View style={styles.envTileHeader}>
                <Sun size={24} color={theme.colors.vibrantPink} />
                <Text style={styles.envTileLabel}>Exposure</Text>
              </View>
              <Text style={styles.envTileValue}>{environmentData?.exposure || '--'}</Text>
            </View>
            <View style={styles.envTile}>
              <View style={styles.envTileHeader}>
                <Thermometer size={24} color={theme.colors.tertiary} />
                <Text style={styles.envTileLabel}>Temp</Text>
              </View>
              <Text style={styles.envTileValue}>
                {environmentData === null ? (
                  <ActivityIndicator size="small" color={theme.colors.primary} />
                ) : environmentData.temperature}
              </Text>
            </View>
            <View style={styles.envTile}>
              <View style={styles.envTileHeader}>
                <Sparkles size={24} color={theme.colors.vibrantPink} />
                <Text style={styles.envTileLabel}>Vibrancy</Text>
              </View>
              <Text style={styles.envTileValue}>{environmentData?.vibrancy || '--'}</Text>
            </View>
          </View>

          {selectedGarden.status === 'Ready' && (
            <View style={{ paddingHorizontal: theme.spacing.margin, marginTop: 10 }}>
              <View style={[styles.analysisContainer, { backgroundColor: theme.colors.surfaceContainerLowest, flexDirection: 'column', alignItems: 'flex-start' }]}>
                <Text style={[styles.analysisText, { color: theme.colors.primary, fontFamily: 'Manrope_700Bold' }]}>Garden Overview</Text>
                <Text style={[styles.analysisText, { marginTop: 4, color: theme.colors.onSurface }]}>{selectedGarden.recommendation}</Text>
                
                {!!selectedGarden.immediate_changes && (
                  <>
                    <Text style={[styles.analysisText, { marginTop: 16, color: theme.colors.vibrantPink, fontFamily: 'Manrope_700Bold' }]}>Immediate Changes</Text>
                    <Text style={[styles.analysisText, { marginTop: 4, color: theme.colors.onSurface }]}>{selectedGarden.immediate_changes}</Text>
                  </>
                )}
                
                {!!selectedGarden.disease_overview && (
                  <>
                    <Text style={[styles.analysisText, { marginTop: 16, color: theme.colors.tertiary, fontFamily: 'Manrope_700Bold' }]}>Disease Overview</Text>
                    <Text style={[styles.analysisText, { marginTop: 4, color: theme.colors.onSurface }]}>{selectedGarden.disease_overview}</Text>
                  </>
                )}

                {!!selectedGarden.growth_trend && (
                  <>
                    <Text style={[styles.analysisText, { marginTop: 16, color: theme.colors.primary, fontFamily: 'Manrope_700Bold' }]}>Growth Trend</Text>
                    <Text style={[styles.analysisText, { marginTop: 4, color: theme.colors.onSurface }]}>{selectedGarden.growth_trend}</Text>
                  </>
                )}
              </View>
            </View>
          )}

          <View style={[styles.header, { marginTop: 20, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}>
            <Text style={[styles.title, { fontSize: 28, marginBottom: 0 }]}>Botanical Residents</Text>
            {uploadingState ? (
              <ActivityIndicator size="small" color={theme.colors.primary} />
            ) : (
              <TouchableOpacity onPress={handleAddPlants} style={{ padding: 8, backgroundColor: theme.colors.surfaceContainerHigh, borderRadius: 20 }}>
                <Plus size={20} color={theme.colors.primary} />
              </TouchableOpacity>
            )}
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingRight: theme.spacing.margin }}
            snapToInterval={CARD_WIDTH - 4}
            decelerationRate="fast"
          >
            {selectedGarden.plants.length > 0 ? (
              selectedGarden.plants.map((plant, index) => (
                <PlantCard key={plant.id} plant={plant} index={index} gardenStatus={selectedGarden.status} onPress={setSelectedPlant} />
              ))
            ) : (
              <View style={[styles.loadingContainer, { width: width - 48, height: 300 }]}>
                <Leaf size={40} color={theme.colors.outline} opacity={0.3} />
                <Text style={styles.loadingText}>No residents yet</Text>
              </View>
            )}
          </ScrollView>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
  loadingText: {
    marginTop: 16,
    color: theme.colors.primary,
    fontFamily: 'Manrope_600SemiBold',
  },
  header: {
    padding: theme.spacing.margin,
    marginTop: 20,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  logoText: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 12,
    letterSpacing: 1.2,
    color: theme.colors.primary,
    marginLeft: 6,
  },
  title: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 34,
    color: theme.colors.primary,
  },
  subtitle: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 14,
    color: theme.colors.primary,
    opacity: 0.6,
  },
  card: {
    width: CARD_WIDTH,
    backgroundColor: 'white',
    borderRadius: theme.roundness.xl,
    overflow: 'hidden',
    shadowColor: theme.colors.primary,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.05,
    shadowRadius: 20,
    elevation: 5,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(85, 97, 88, 0.05)',
  },
  cardImage: {
    width: '100%',
    height: 300,
    backgroundColor: theme.colors.surfaceContainerLowest,
  },
  cardContent: {
    padding: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  gardenName: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 18,
    color: theme.colors.primary,
    flex: 1,
    marginRight: 10,
  },
  statusChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  statusReady: {
    backgroundColor: theme.colors.primaryContainer,
  },
  statusProcessing: {
    backgroundColor: '#fff3e0',
  },
  statusText: {
    fontSize: 10,
    fontFamily: 'Manrope_700Bold',
    color: theme.colors.tertiary,
    textTransform: 'uppercase',
  },
  recommendation: {
    fontFamily: 'Manrope_400Regular',
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: theme.colors.surfaceContainer,
  },
  footerText: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 13,
    color: theme.colors.primary,
    flex: 1,
  },
  plantVariety: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 11,
    color: theme.colors.tertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  conditionBadge: {
    backgroundColor: '#f1f8e9',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  conditionText: {
    color: '#2e7d32',
    fontFamily: 'Manrope_700Bold',
    fontSize: 11,
  },
  plantStats: {
    flexDirection: 'row',
    gap: 15,
    marginTop: 20,
    paddingTop: 15,
    borderTopWidth: 1,
    borderTopColor: theme.colors.surfaceContainer,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  statText: {
    fontFamily: 'Manrope_400Regular',
    fontSize: 12,
    color: theme.colors.outline,
  },
  progressBarContainer: {
    paddingHorizontal: theme.spacing.margin,
    marginTop: 10,
    marginBottom: 40,
  },
  progressBar: {
    height: 3,
    backgroundColor: theme.colors.surfaceContainer,
    borderRadius: 2,
    position: 'relative',
    overflow: 'hidden',
  },
  progressIndicator: {
    position: 'absolute',
    top: 0,
    left: 0,
    height: '100%',
    backgroundColor: theme.colors.primary,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.margin,
    paddingBottom: 0,
  },
  backText: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 14,
    color: theme.colors.primary,
    marginLeft: 8,
  },

  inputGroup: {
    marginBottom: 24,
  },
  inputLabel: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 14,
    color: theme.colors.primary,
    marginBottom: 8,
  },
  textInput: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: theme.colors.outline,
    borderRadius: theme.roundness.md,
    padding: theme.spacing.md,
    fontFamily: 'Manrope_400Regular',
    fontSize: 16,
    color: theme.colors.onSurface,
  },
  locationInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.surfaceContainer,
  },
  suggestionsContainer: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: theme.colors.outlineVariant + '4D',
    borderBottomLeftRadius: theme.roundness.md,
    borderBottomRightRadius: theme.roundness.md,
    borderTopWidth: 0,
    marginTop: -4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3,
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    zIndex: 20,
    maxHeight: 150,
  },
  suggestionItem: {
    padding: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.surfaceContainer,
  },
  suggestionText: {
    fontFamily: 'Manrope_400Regular',
    fontSize: 14,
    color: theme.colors.onSurface,
  },
  uploadZone: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: theme.colors.surfaceContainerHigh,
    borderRadius: theme.roundness.lg,
    padding: 40,
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
  uploadText: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 16,
    color: theme.colors.primary,
    marginBottom: 4,
  },
  uploadSubtext: {
    fontFamily: 'Manrope_400Regular',
    fontSize: 12,
    color: theme.colors.outline,
  },
  btnPrimary: {
    backgroundColor: theme.colors.secondaryContainer,
    borderRadius: 48,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 32,
    gap: 8,
  },
  btnPrimaryText: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 16,
    color: theme.colors.onSecondaryContainer,
  },
  btnIcon: {
    backgroundColor: theme.colors.primaryContainer,
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tilesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: theme.spacing.margin,
    gap: 16,
    marginBottom: 24,
  },
  envTile: {
    backgroundColor: theme.colors.surfaceContainerLow,
    borderRadius: theme.roundness.lg,
    borderWidth: 1,
    borderColor: theme.colors.outlineVariant + '4D',
    padding: 24,
    flexDirection: 'column',
    width: (width - (theme.spacing.margin * 2) - 16) / 2,
    gap: 4,
  },
  envTileHeader: {
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: 4,
  },
  envTileLabel: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 13,
    color: theme.colors.onSurfaceVariant,
  },
  envTileValue: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 24,
    color: theme.colors.onSurface,
  },
  heroContainer: {
    marginHorizontal: theme.spacing.margin,
    marginTop: theme.spacing.sm,
    height: 320,
    borderRadius: 32,
    overflow: 'hidden',
    position: 'relative',
    borderWidth: 1,
    borderColor: theme.colors.outlineVariant + '4D',
  },
  heroImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  heroOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: theme.spacing.md,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  heroTitle: {
    fontFamily: 'Manrope_700Bold',
    fontSize: 32,
    color: '#ffffff',
  },
  heroLocation: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 14,
    color: '#ffffff',
    opacity: 0.9,
    marginTop: 4,
  },
  analysisContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.primaryContainer,
    marginHorizontal: theme.spacing.margin,
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.md,
    padding: theme.spacing.md,
    borderRadius: theme.roundness.lg,
    gap: 12,
  },
  analysisText: {
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 14,
    color: theme.colors.onSurfaceVariant,
    flexShrink: 1,
  },
});
