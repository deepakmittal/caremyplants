const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'mobile', 'App.js');
let content = fs.readFileSync(filePath, 'utf8');

// 1. Imports
content = content.replace(
  /import {[\s\S]*?} from 'react-native';/,
  `import {
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
  Platform
} from 'react-native';`
);

content = content.replace(
  /import { getDetailedGardens } from '\.\/src\/services\/api';/,
  `import { getDetailedGardens, uploadGardenPhotos } from './src/services/api';`
);

content = content.replace(
  /import { Leaf, ChevronRight, ArrowLeft, Droplets, Sun } from 'lucide-react-native';/,
  `import { Leaf, ChevronRight, ArrowLeft, Droplets, Sun, Plus, Image as ImageIcon, Sparkles } from 'lucide-react-native';\nimport * as ImagePicker from 'expo-image-picker';`
);

// 2. State variables inside App
content = content.replace(
  /const \[scrollX, setScrollX\] = useState\(0\);/,
  `const [scrollX, setScrollX] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadData, setUploadData] = useState({ name: '', photos: [] });
  const [uploadingState, setUploadingState] = useState(false);`
);

// 3. Handlers
content = content.replace(
  /const fetchData = async \(\) => {/,
  `const pickImage = async () => {
    let result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsMultipleSelection: true,
      quality: 0.8,
    });

    if (!result.canceled) {
      setUploadData({ ...uploadData, photos: result.assets });
    }
  };

  const handleUploadSubmit = async () => {
    if (!uploadData.name || uploadData.photos.length === 0) return;
    
    setUploadingState(true);
    try {
      await uploadGardenPhotos(uploadData.photos, uploadData.name, 4);
      setUploadData({ name: '', photos: [] });
      setIsUploading(false);
      await fetchData();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload garden. Please try again.");
    } finally {
      setUploadingState(false);
    }
  };

  const fetchData = async () => {`
);

// 4. Render
const renderUploadScreen = `
      {isUploading ? (
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
            <Text style={[styles.title, { fontSize: 28 }]}>Capture Sanctuary</Text>
          </View>

          <ScrollView contentContainerStyle={{ paddingHorizontal: theme.spacing.margin }}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Sanctuary Name</Text>
              <TextInput
                style={styles.textInput}
                placeholder="e.g. Sunny Balcony, Indoor Jungle"
                value={uploadData.name}
                onChangeText={(text) => setUploadData({ ...uploadData, name: text })}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Plant Photos</Text>
              <TouchableOpacity style={styles.uploadZone} onPress={pickImage}>
                <ImageIcon size={40} color={theme.colors.outline} style={{ marginBottom: 16 }} />
                <Text style={styles.uploadText}>
                  {uploadData.photos.length > 0 
                    ? \`\${uploadData.photos.length} photos selected\` 
                    : "Tap to select photos"}
                </Text>
                <Text style={styles.uploadSubtext}>High-res JPG or PNG works best</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity 
              style={[styles.btnPrimary, (uploadingState || uploadData.photos.length === 0 || !uploadData.name) && { opacity: 0.5 }]}
              onPress={handleUploadSubmit}
              disabled={uploadingState || uploadData.photos.length === 0 || !uploadData.name}
            >
              {uploadingState ? (
                <ActivityIndicator color={theme.colors.onSecondaryContainer} size="small" />
              ) : (
                <Sparkles size={20} color={theme.colors.onSecondaryContainer} />
              )}
              <Text style={styles.btnPrimaryText}>
                {uploadingState ? 'Analyzing...' : 'Initialize AI Analysis'}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      ) : !selectedGarden ? (
`;

// Replace `{!selectedGarden ? (` with `renderUploadScreen`
content = content.replace(
  /\{\!selectedGarden \? \(/,
  renderUploadScreen
);

// 5. Update My Sanctuaries Header to include Plus button
const headerString = `<View style={styles.header}>
            <View style={styles.logoContainer}>
              <Leaf size={18} color={theme.colors.primary} />
              <Text style={styles.logoText}>BOTANICAL MANAGER</Text>
            </View>
            <Text style={styles.title}>My Sanctuaries</Text>
          </View>`;

const newHeaderString = `<View style={[styles.header, { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }]}>
            <View>
              <View style={styles.logoContainer}>
                <Leaf size={18} color={theme.colors.primary} />
                <Text style={styles.logoText}>BOTANICAL MANAGER</Text>
              </View>
              <Text style={styles.title}>My Sanctuaries</Text>
            </View>
            <TouchableOpacity style={styles.btnIcon} onPress={() => setIsUploading(true)}>
              <Plus size={24} color={theme.colors.tertiary} />
            </TouchableOpacity>
          </View>`;

content = content.replace(headerString, newHeaderString);

// 6. Add CSS to styles
const extraStyles = `
  inputGroup: {
    marginBottom: 24,
  },
  inputLabel: {
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 14,
    color: theme.colors.primary,
    marginBottom: 8,
  },
  textInput: {
    borderWidth: 1,
    borderColor: theme.colors.surfaceContainerHigh,
    borderRadius: theme.roundness.md,
    padding: 16,
    fontFamily: 'PlusJakartaSans_400Regular',
    fontSize: 16,
    color: theme.colors.primary,
    backgroundColor: theme.colors.background,
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
    fontFamily: 'PlusJakartaSans_600SemiBold',
    fontSize: 16,
    color: theme.colors.primary,
    marginBottom: 4,
  },
  uploadSubtext: {
    fontFamily: 'PlusJakartaSans_400Regular',
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
    fontFamily: 'PlusJakartaSans_700Bold',
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
});`;

content = content.replace(/\}\);/g, (match, offset, string) => {
  if (offset === string.lastIndexOf('});')) {
    return extraStyles;
  }
  return match;
});

fs.writeFileSync(filePath, content);
console.log('App.js patched successfully');
