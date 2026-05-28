import React, { useState, useEffect } from 'react';
import { View, Text, Image, ScrollView, TouchableOpacity, ActivityIndicator, StyleSheet, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { theme } from '../theme';
import { getPlantUpdates, uploadPlantPhoto } from '../services/api';
import { ArrowLeft, Clock, Image as ImageIcon, UploadCloud } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';

const { width } = Dimensions.get('window');

export default function PlantDetails({ plant, onBack, onUpdate }) {
  const [updates, setUpdates] = useState([]);
  const [loadingUpdates, setLoadingUpdates] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    if (showTimeline) {
      loadUpdates();
    }
  }, [showTimeline]);

  const loadUpdates = async () => {
    setLoadingUpdates(true);
    try {
      const data = await getPlantUpdates(plant.id);
      setUpdates(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingUpdates(false);
    }
  };

  const handleUpload = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('Sorry, we need camera roll permissions to make this work!');
      return;
    }

    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setIsUploading(true);
      try {
        await uploadPlantPhoto(plant.id, result.assets[0]);
        if (onUpdate) onUpdate();
        alert("Photo uploaded successfully! The AI is analyzing it in the background.");
      } catch (err) {
        alert("Failed to upload photo. Please try again.");
      } finally {
        setIsUploading(false);
      }
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <ArrowLeft size={24} color={theme.colors.onSurface} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{plant.name}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.imageContainer}>
          {plant.image_url ? (
            <Image source={{ uri: plant.image_url }} style={styles.image} resizeMode="cover" />
          ) : (
            <View style={[styles.image, { justifyContent: 'center', alignItems: 'center', backgroundColor: theme.colors.surfaceContainerHigh }]}>
              <ImageIcon size={48} color={theme.colors.outline} />
            </View>
          )}
        </View>

        <View style={styles.content}>
          <Text style={styles.variety}>{plant.plant_variety || 'Unknown Species'}</Text>
          <Text style={styles.conditionTitle}>Current Condition</Text>
          <View style={styles.conditionBadge}>
            <Text style={styles.conditionText}>{plant.latest_condition || 'Healthy'}</Text>
          </View>
          <Text style={styles.recommendation}>
            {plant.latest_recommendation || "Maintain consistent care to ensure your plant thrives in its current environment."}
          </Text>

          <View style={styles.actions}>
            <TouchableOpacity style={styles.primaryButton} onPress={handleUpload} disabled={isUploading}>
              {isUploading ? (
                <ActivityIndicator color={theme.colors.onPrimary} />
              ) : (
                <>
                  <UploadCloud size={20} color={theme.colors.onPrimary} />
                  <Text style={styles.primaryButtonText}>Upload Better Photo</Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity style={styles.secondaryButton} onPress={() => setShowTimeline(!showTimeline)}>
              <Clock size={20} color={theme.colors.primary} />
              <Text style={styles.secondaryButtonText}>{showTimeline ? 'Hide Timeline' : 'Show Timeline'}</Text>
            </TouchableOpacity>
          </View>

          {showTimeline && (
            <View style={styles.timelineContainer}>
              <Text style={styles.timelineHeader}>Plant History</Text>
              {loadingUpdates ? (
                <ActivityIndicator size="large" color={theme.colors.primary} style={{ marginTop: 20 }} />
              ) : updates.length === 0 ? (
                <Text style={styles.emptyText}>No history available yet.</Text>
              ) : (
                updates.map((update, index) => (
                  <View key={update.id} style={styles.timelineItem}>
                    <View style={styles.timelineLine} />
                    <View style={styles.timelineDot} />
                    <View style={styles.timelineCard}>
                      <Text style={styles.timelineDate}>{new Date(update.created_at).toLocaleDateString()}</Text>
                      {!!update.image_url && (
                        <Image source={{ uri: update.image_url }} style={{ width: '100%', height: 150, borderRadius: 8, marginBottom: 12 }} resizeMode="cover" />
                      )}
                      <View style={styles.conditionBadgeSmall}>
                        <Text style={styles.conditionTextSmall}>{update.condition_text}</Text>
                      </View>
                      <Text style={styles.timelineRec}>{update.recommendation}</Text>
                      {!!update.changes_from_previous && (
                         <View style={{ marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: theme.colors.surfaceContainerHigh }}>
                            <Text style={{ fontSize: 14, fontFamily: 'Manrope_700Bold', color: theme.colors.primary, marginBottom: 4 }}>Changes Since Last Update</Text>
                            <Text style={{ fontSize: 14, fontFamily: 'Manrope_400Regular', color: theme.colors.onSurfaceVariant, lineHeight: 20 }}>{update.changes_from_previous}</Text>
                         </View>
                      )}
                    </View>
                  </View>
                ))
              )}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.surface,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.margin,
    paddingVertical: 16,
    backgroundColor: theme.colors.surface,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: theme.colors.surfaceContainer,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontFamily: 'Manrope_700Bold',
    color: theme.colors.onSurface,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  imageContainer: {
    width: '100%',
    height: width * 0.8,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  content: {
    padding: theme.spacing.margin,
  },
  variety: {
    fontSize: 16,
    fontFamily: 'Manrope_600SemiBold',
    color: theme.colors.outline,
    marginBottom: 16,
  },
  conditionTitle: {
    fontSize: 18,
    fontFamily: 'Manrope_700Bold',
    color: theme.colors.onSurface,
    marginBottom: 8,
  },
  conditionBadge: {
    backgroundColor: theme.colors.secondaryContainer,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    marginBottom: 16,
  },
  conditionText: {
    color: theme.colors.onSecondaryContainer,
    fontFamily: 'Manrope_700Bold',
    fontSize: 14,
  },
  recommendation: {
    fontSize: 16,
    fontFamily: 'Manrope_400Regular',
    color: theme.colors.onSurfaceVariant,
    lineHeight: 24,
    marginBottom: 24,
  },
  actions: {
    gap: 12,
    marginBottom: 32,
  },
  primaryButton: {
    backgroundColor: theme.colors.primary,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  primaryButtonText: {
    color: theme.colors.onPrimary,
    fontFamily: 'Manrope_700Bold',
    fontSize: 16,
  },
  secondaryButton: {
    backgroundColor: theme.colors.surfaceContainer,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  secondaryButtonText: {
    color: theme.colors.primary,
    fontFamily: 'Manrope_700Bold',
    fontSize: 16,
  },
  timelineContainer: {
    marginTop: 8,
  },
  timelineHeader: {
    fontSize: 20,
    fontFamily: 'Manrope_700Bold',
    color: theme.colors.onSurface,
    marginBottom: 24,
  },
  emptyText: {
    fontSize: 14,
    color: theme.colors.outline,
    fontFamily: 'Manrope_400Regular',
    textAlign: 'center',
    marginTop: 20,
  },
  timelineItem: {
    flexDirection: 'row',
    marginBottom: 24,
    position: 'relative',
  },
  timelineLine: {
    position: 'absolute',
    left: 7,
    top: 24,
    bottom: -24,
    width: 2,
    backgroundColor: theme.colors.surfaceContainerHigh,
  },
  timelineDot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: theme.colors.primary,
    marginTop: 4,
    marginRight: 16,
    borderWidth: 3,
    borderColor: theme.colors.surfaceContainerHigh,
  },
  timelineCard: {
    flex: 1,
    backgroundColor: theme.colors.surfaceContainer,
    padding: 16,
    borderRadius: 12,
  },
  timelineDate: {
    fontSize: 12,
    fontFamily: 'Manrope_600SemiBold',
    color: theme.colors.outline,
    marginBottom: 8,
  },
  conditionBadgeSmall: {
    backgroundColor: theme.colors.secondaryContainer,
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginBottom: 8,
  },
  conditionTextSmall: {
    color: theme.colors.onSecondaryContainer,
    fontFamily: 'Manrope_600SemiBold',
    fontSize: 12,
  },
  timelineRec: {
    fontSize: 14,
    fontFamily: 'Manrope_400Regular',
    color: theme.colors.onSurfaceVariant,
    lineHeight: 20,
  },
});
